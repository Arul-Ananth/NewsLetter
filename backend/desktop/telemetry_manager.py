from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime

from PySide6.QtWidgets import QApplication, QTextEdit

from backend.common.config import settings
from backend.common.services.telemetry import (
    DocumentIngestionWorker,
    EventBus,
    EventPriority,
    SessionSummaryWorker,
    TelemetryDispatcher,
    TelemetryEvent,
    UserProfileRollupWorker,
)
from backend.common.services.telemetry.consent import get_consented_folders
from backend.common.services.memory.vector_db import client as qdrant_client
from backend.desktop.collectors import ClipboardCollector, FileDropCollector, FolderWatchCollector, ReaderTelemetryCollector
from backend.desktop.preferences import get_clipboard_collection_enabled, get_data_collection_enabled

logger = logging.getLogger(__name__)


class TelemetryManager:
    def __init__(self, user_id: int, session_id: str, output: QTextEdit) -> None:
        self.user_id = user_id
        self.session_id = session_id
        self.output = output

        self.event_bus: EventBus | None = None
        self.ingestion_queue: asyncio.Queue | None = None
        self.summary_queue: asyncio.Queue | None = None
        self.dispatcher: TelemetryDispatcher | None = None
        self.profile_worker: UserProfileRollupWorker | None = None
        self.ingestion_worker: DocumentIngestionWorker | None = None
        self.summary_worker: SessionSummaryWorker | None = None

        self.clipboard_collector = ClipboardCollector(QApplication.clipboard(), session_id, self.emit)
        self.file_drop_collector = FileDropCollector(session_id, user_id, self.emit)
        self.folder_watch_collector = FolderWatchCollector(session_id, user_id, self.emit)
        self.reader_telemetry = ReaderTelemetryCollector(output, session_id, self.emit)

        self._data_collection_enabled = settings.DATA_COLLECTION_ENABLED
        self._loop: asyncio.AbstractEventLoop | None = None
        self._runtime_thread: threading.Thread | None = None
        self._runtime_ready = threading.Event()
        self._tasks: list[asyncio.Task] = []

    def start(self) -> None:
        self._data_collection_enabled = get_data_collection_enabled()
        if not self._data_collection_enabled:
            logger.info("Desktop telemetry collection disabled by user preference.")
            return

        try:
            self._start_runtime()
        except Exception as exc:
            logger.exception("Failed to start telemetry runtime: %s", exc)
            return

        clipboard_collection_enabled = get_clipboard_collection_enabled()
        self.reader_telemetry.start()
        if clipboard_collection_enabled:
            self.clipboard_collector.start()

        if settings.FOLDER_WATCH_ENABLED:
            folders = get_consented_folders()
            self.folder_watch_collector.start(folders)

        self.emit_session_start()

    def shutdown(self) -> None:
        self.folder_watch_collector.stop()
        if self._data_collection_enabled:
            if self._loop and self._runtime_ready.is_set():
                future = asyncio.run_coroutine_threadsafe(self._drain_and_stop(), self._loop)
                try:
                    future.result(timeout=10)
                except Exception as exc:
                    logger.warning("Telemetry drain timed out or failed: %s", exc)
                self._loop.call_soon_threadsafe(self._loop.stop)

            if self._runtime_thread:
                self._runtime_thread.join(timeout=3)

        try:
            qdrant_client.close()
        except Exception:
            pass

    def emit(self, event: TelemetryEvent) -> None:
        if not self._data_collection_enabled:
            return
        if not self._loop or not self._runtime_ready.is_set() or self.event_bus is None:
            logger.debug("Dropping telemetry event before runtime is ready: %s", event.event_type)
            return
        self._loop.call_soon_threadsafe(self.event_bus.enqueue, event)

    def emit_session_start(self) -> None:
        payload = {"ts": datetime.utcnow().isoformat(), "user_id": self.user_id}
        event = TelemetryEvent(
            event_type="session_start",
            session_id=self.session_id,
            payload=payload,
            source="session",
            priority=EventPriority.CRITICAL,
        )
        self.emit(event)

    def emit_session_end(self) -> None:
        payload = {"ts": datetime.utcnow().isoformat(), "user_id": self.user_id}
        event = TelemetryEvent(
            event_type="session_end",
            session_id=self.session_id,
            payload=payload,
            source="session",
            priority=EventPriority.CRITICAL,
        )
        self.emit(event)

    def emit_generation(self, topic: str, context: str) -> None:
        payload = {
            "topic": topic,
            "context": context,
            "user_id": self.user_id,
            "ts": datetime.utcnow().isoformat(),
        }
        event = TelemetryEvent(
            event_type="generate_newsletter",
            session_id=self.session_id,
            payload=payload,
            source="ui",
            priority=EventPriority.CRITICAL,
        )
        self.emit(event)

    def mark_output_start(self) -> None:
        if not self._data_collection_enabled:
            return
        self.reader_telemetry.mark_output_start()

    def flush_output_time(self) -> None:
        if not self._data_collection_enabled:
            return
        self.reader_telemetry.flush_output_time()

    def handle_file_drop(self, paths: list[str]) -> None:
        if not self._data_collection_enabled:
            return
        self.file_drop_collector.handle_paths(paths)

    def _start_runtime(self) -> None:
        if self._runtime_thread and self._runtime_thread.is_alive():
            return

        self._runtime_ready.clear()
        self._runtime_thread = threading.Thread(target=self._run_runtime_loop, name="TelemetryRuntime", daemon=True)
        self._runtime_thread.start()
        if not self._runtime_ready.wait(timeout=5):
            raise RuntimeError("Telemetry runtime failed to start in time.")

    def _run_runtime_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop

        self.event_bus = EventBus(settings.EVENT_QUEUE_MAX)
        self.ingestion_queue = asyncio.Queue(maxsize=200)
        self.summary_queue = asyncio.Queue(maxsize=50)

        self.dispatcher = TelemetryDispatcher(self.event_bus, self.ingestion_queue, self.summary_queue)
        self.profile_worker = UserProfileRollupWorker()
        self.ingestion_worker = DocumentIngestionWorker(self.ingestion_queue)
        self.summary_worker = SessionSummaryWorker(self.summary_queue, self.profile_worker)

        self._tasks = [
            loop.create_task(self.dispatcher.run()),
            loop.create_task(self.ingestion_worker.run()),
            loop.create_task(self.summary_worker.run()),
        ]
        self._runtime_ready.set()

        try:
            loop.run_forever()
        finally:
            pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    async def _drain_and_stop(self) -> None:
        if not self.event_bus or not self.ingestion_queue or not self.summary_queue:
            return

        try:
            await asyncio.wait_for(self.event_bus.queue.join(), timeout=3)
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for telemetry event queue to drain.")

        try:
            await asyncio.wait_for(self.ingestion_queue.join(), timeout=5)
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for ingestion queue to drain.")

        try:
            await asyncio.wait_for(self.summary_queue.join(), timeout=5)
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for summary queue to drain.")

        if self.dispatcher:
            self.dispatcher.stop()
        if self.ingestion_worker:
            self.ingestion_worker.stop()
        if self.summary_worker:
            self.summary_worker.stop()

        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
