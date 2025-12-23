"""Shared database setup."""
from sqlmodel import Session, SQLModel, create_engine

from backend.common.config import settings

# Unified DB Path
sqlite_file_name = "aerobrief.db"
sqlite_url = f"sqlite:///{settings.DATA_DIR / sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables() -> None:
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
