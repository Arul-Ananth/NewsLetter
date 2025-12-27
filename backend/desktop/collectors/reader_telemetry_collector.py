from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QTextEdit

from backend.common.services.telemetry.event_bus import EventPriority, TelemetryEvent


class ReaderTelemetryCollector(QObject):
    def __init__(self, output: QTextEdit, session_id: str, emit: Callable[[TelemetryEvent], None]) -> None:
        super().__init__()
        self.output = output
        self.session_id = session_id
        self.emit = emit
        self._output_start: float | None = None
        self._last_scroll_emit = 0.0
        self._max_scroll = 0.0

    def start(self) -> None:
        self.output.installEventFilter(self)
        self.output.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def mark_output_start(self) -> None:
        self._output_start = time.time()
        self._max_scroll = 0.0

    def flush_output_time(self) -> None:
        if self._output_start is None:
            return
        seconds = max(time.time() - self._output_start, 0.0)
        payload = {"seconds": seconds, "ts": datetime.utcnow().isoformat()}
        event = TelemetryEvent(
            event_type="telemetry_output_time",
            session_id=self.session_id,
            payload=payload,
            source="output",
            priority=EventPriority.TELEMETRY,
        )
        self.emit(event)
        self._output_start = None

    def _on_scroll(self, value: int) -> None:
        now = time.time()
        if now - self._last_scroll_emit < 1.0:
            return
        scrollbar = self.output.verticalScrollBar()
        maximum = max(scrollbar.maximum(), 1)
        depth = min(value / maximum, 1.0)
        self._max_scroll = max(self._max_scroll, depth)
        payload = {"depth": self._max_scroll, "ts": datetime.utcnow().isoformat()}
        event = TelemetryEvent(
            event_type="telemetry_scroll",
            session_id=self.session_id,
            payload=payload,
            source="output",
            priority=EventPriority.TELEMETRY,
        )
        self.emit(event)
        self._last_scroll_emit = now

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.output and event.type() == QEvent.KeyPress:
            key_event = event  # type: ignore[assignment]
            if isinstance(key_event, QKeyEvent) and key_event.matches(QKeySequence.Copy):
                payload = {"ts": datetime.utcnow().isoformat()}
                event_obj = TelemetryEvent(
                    event_type="telemetry_copy",
                    session_id=self.session_id,
                    payload=payload,
                    source="output",
                    priority=EventPriority.IMPORTANT,
                )
                self.emit(event_obj)
        return super().eventFilter(watched, event)
