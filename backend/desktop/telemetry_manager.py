from __future__ import annotations

import asyncio
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
from backend.common.services.vector_db import client as qdrant_client
from backend.desktop.collectors import ClipboardCollector, FileDropCollector, FolderWatchCollector, ReaderTelemetryCollector

class TelemetryManager:
    def __init__(self, user_id: int, session_id: str, output: QTextEdit) -> None:
        self.user_id = user_id
        self.session_id = session_id
        self.output = output

        self.event_bus = EventBus(settings.EVENT_QUEUE_MAX)
        self.ingestion_queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self.summary_queue: asyncio.Queue = asyncio.Queue(maxsize=50)

        self.dispatcher = TelemetryDispatcher(self.event_bus, self.ingestion_queue, self.summary_queue)
        self.profile_worker = UserProfileRollupWorker()
        self.ingestion_worker = DocumentIngestionWorker(self.ingestion_queue)
        self.summary_worker = SessionSummaryWorker(self.summary_queue, self.profile_worker)

        self.clipboard_collector = ClipboardCollector(QApplication.clipboard(), session_id, self.emit)
        self.file_drop_collector = FileDropCollector(session_id, user_id, self.emit)
        self.folder_watch_collector = FolderWatchCollector(session_id, user_id, self.emit)
        self.reader_telemetry = ReaderTelemetryCollector(output, session_id, self.emit)

        self._tasks: list[asyncio.Task] = []

    def start(self) -> None:
        loop = asyncio.get_event_loop()
        self._tasks.append(loop.create_task(self.dispatcher.run()))
        self._tasks.append(loop.create_task(self.ingestion_worker.run()))
        self._tasks.append(loop.create_task(self.summary_worker.run()))

        if settings.DATA_COLLECTION_ENABLED:
            self.clipboard_collector.start()
            self.reader_telemetry.start()

        if settings.FOLDER_WATCH_ENABLED:
            folders = get_consented_folders()
            self.folder_watch_collector.start(folders)

        self.emit_session_start()

    def shutdown(self) -> None:
        self.folder_watch_collector.stop()
        self.dispatcher.stop()
        self.ingestion_worker.stop()
        self.summary_worker.stop()
        for task in self._tasks:
            task.cancel()
        try:
            qdrant_client.close()
        except Exception:
            pass

    def emit(self, event: TelemetryEvent) -> None:
        self.event_bus.enqueue(event)

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
        self.reader_telemetry.mark_output_start()

    def flush_output_time(self) -> None:
        self.reader_telemetry.flush_output_time()

    def handle_file_drop(self, paths: list[str]) -> None:
        self.file_drop_collector.handle_paths(paths)
