from __future__ import annotations

import asyncio
import logging
import threading

from backend.common.config import settings
from backend.common.services.telemetry import (
    DocumentIngestionWorker,
    EventBus,
    SessionSummaryWorker,
    TelemetryDispatcher,
    TelemetryEvent,
    UserProfileRollupWorker,
)

logger = logging.getLogger(__name__)


class TelemetryRuntime:
    def __init__(self) -> None:
        self.event_bus: EventBus | None = None
        self.ingestion_queue: asyncio.Queue | None = None
        self.summary_queue: asyncio.Queue | None = None
        self.dispatcher: TelemetryDispatcher | None = None
        self.profile_worker: UserProfileRollupWorker | None = None
        self.ingestion_worker: DocumentIngestionWorker | None = None
        self.summary_worker: SessionSummaryWorker | None = None

        self._loop: asyncio.AbstractEventLoop | None = None
        self._runtime_thread: threading.Thread | None = None
        self._runtime_ready = threading.Event()
        self._tasks: list[asyncio.Task] = []

    @property
    def is_ready(self) -> bool:
        return self._loop is not None and self._runtime_ready.is_set() and self.event_bus is not None

    def start(self) -> None:
        if self._runtime_thread and self._runtime_thread.is_alive():
            return

        self._runtime_ready.clear()
        self._runtime_thread = threading.Thread(target=self._run_runtime_loop, name='TelemetryRuntime', daemon=True)
        self._runtime_thread.start()
        if not self._runtime_ready.wait(timeout=5):
            raise RuntimeError('Telemetry runtime failed to start in time.')

    def enqueue(self, event: TelemetryEvent) -> None:
        if not self.is_ready or not self.event_bus or not self._loop:
            logger.debug('Dropping telemetry event before runtime is ready: %s', event.event_type)
            return
        self._loop.call_soon_threadsafe(self.event_bus.enqueue, event)

    def shutdown(self) -> None:
        if self._loop and self._runtime_ready.is_set():
            future = asyncio.run_coroutine_threadsafe(self._drain_and_stop(), self._loop)
            try:
                future.result(timeout=10)
            except Exception as exc:
                logger.warning('Telemetry drain timed out or failed: %s', exc)
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._runtime_thread:
            self._runtime_thread.join(timeout=3)

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
            logger.warning('Timed out waiting for telemetry event queue to drain.')

        try:
            await asyncio.wait_for(self.ingestion_queue.join(), timeout=5)
        except asyncio.TimeoutError:
            logger.warning('Timed out waiting for ingestion queue to drain.')

        try:
            await asyncio.wait_for(self.summary_queue.join(), timeout=5)
        except asyncio.TimeoutError:
            logger.warning('Timed out waiting for summary queue to drain.')

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
