from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

from backend.common.services.telemetry.event_bus import EventPriority, TelemetryEvent

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt", ".html"}


class FileDropCollector:
    def __init__(self, session_id: str, user_id: int, emit: Callable[[TelemetryEvent], None]) -> None:
        self.session_id = session_id
        self.user_id = user_id
        self.emit = emit

    def handle_paths(self, paths: list[str]) -> None:
        for raw in paths:
            path = Path(raw)
            if not path.exists():
                continue
            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                logger.info("Skipping unsupported file drop: %s", path)
                continue
            payload = {
                "path": str(path),
                "user_id": self.user_id,
                "ts": datetime.utcnow().isoformat(),
                "consent": "implicit_drag_drop",
            }
            event = TelemetryEvent(
                event_type="file_ingestion",
                session_id=self.session_id,
                payload=payload,
                source="file_drop",
                priority=EventPriority.CRITICAL,
            )
            self.emit(event)
