from __future__ import annotations

import logging
from pathlib import Path

from sqlmodel import Session, select

from backend.common.database import engine
from backend.common.models.sql import FolderConsent

logger = logging.getLogger(__name__)


def get_consented_folders() -> list[Path]:
    with Session(engine) as session:
        rows = session.exec(select(FolderConsent)).all()
    return [Path(row.path) for row in rows]


def add_folder_consent(path: Path) -> None:
    with Session(engine) as session:
        existing = session.get(FolderConsent, str(path))
        if existing:
            return
        session.add(FolderConsent(path=str(path)))
        session.commit()
        logger.info("Stored folder consent: %s", path)


def has_folder_consent(path: Path) -> bool:
    with Session(engine) as session:
        return session.get(FolderConsent, str(path)) is not None
