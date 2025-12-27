from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

from backend.common.services.telemetry.event_bus import EventPriority, TelemetryEvent
from backend.common.services.telemetry.ingestion import file_sha256

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt", ".html"}


class FolderWatchCollector:
    def __init__(self, session_id: str, user_id: int, emit: Callable[[TelemetryEvent], None]) -> None:
        self.session_id = session_id
        self.user_id = user_id
        self.emit = emit
        self._observer = None
        self._seen: dict[str, tuple[str, float]] = {}

    def start(self, folders: list[Path]) -> None:
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except Exception as exc:
            logger.warning("Folder watch disabled (missing watchdog): %s", exc)
            return

        if not folders:
            return

        collector = self

        class Handler(FileSystemEventHandler):
            def on_modified(self, event):  # type: ignore[override]
                collector._handle_path(event.src_path)

            def on_created(self, event):  # type: ignore[override]
                collector._handle_path(event.src_path)

        handler = Handler()

        observer = Observer()
        for folder in folders:
            observer.schedule(handler, str(folder), recursive=True)
        observer.start()
        self._observer = observer
        logger.info("Folder watch started for %s folders.", len(folders))

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=1)
            self._observer = None

    def _handle_path(self, path_str: str) -> None:
        path = Path(path_str)
        if path.is_dir() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            return
        try:
            content_hash = file_sha256(path)
            mtime = path.stat().st_mtime
        except Exception:
            return
        last = self._seen.get(str(path))
        if last and last == (content_hash, mtime):
            return
        self._seen[str(path)] = (content_hash, mtime)
        payload = {
            "path": str(path),
            "user_id": self.user_id,
            "ts": datetime.utcnow().isoformat(),
            "consent": "folder_watch",
        }
        event_obj = TelemetryEvent(
            event_type="file_ingestion",
            session_id=self.session_id,
            payload=payload,
            source="folder_watch",
            priority=EventPriority.CRITICAL,
            content_hash=content_hash,
        )
        self.emit(event_obj)
