"""Shared database setup."""
from sqlmodel import Session, SQLModel, create_engine

from backend.common.config import settings
from backend.common.models.sql import DerivedMemory

# Unified DB Path
sqlite_file_name = "aerobrief.db"
sqlite_url = f"sqlite:///{settings.DATA_DIR / sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def _run_migrations() -> None:
    if engine.dialect.name != "sqlite":
        return

    table_name = getattr(DerivedMemory, "__tablename__", "derivedmemory")
    with engine.begin() as conn:
        columns = conn.exec_driver_sql(f"PRAGMA table_info('{table_name}')").fetchall()
        column_names = {row[1] for row in columns}
        if "user_id" not in column_names:
            conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN user_id INTEGER DEFAULT -1")
            conn.exec_driver_sql(f"UPDATE {table_name} SET user_id = -1 WHERE user_id IS NULL")
        conn.exec_driver_sql(
            f"CREATE INDEX IF NOT EXISTS ix_{table_name}_user_id ON {table_name}(user_id)"
        )


def create_db_and_tables() -> None:
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    _run_migrations()


def get_session():
    with Session(engine) as session:
        yield session
