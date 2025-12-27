from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    full_name: str = Field(max_length=100)
    hashed_password: str


class UserWallet(SQLModel, table=True):
    user_id: int = Field(primary_key=True, foreign_key="user.id")
    balance: int = Field(default=50)


class UsageLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    topic: str
    input_tokens: int
    output_tokens: int
    total_cost: int


class EventRaw(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str = Field(index=True, max_length=80)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    session_id: str = Field(index=True, max_length=64)
    payload_json: str
    hash: str = Field(index=True, max_length=64)
    source: str = Field(max_length=80)


class FilesIndex(SQLModel, table=True):
    path: str = Field(primary_key=True, max_length=512)
    content_hash: str = Field(max_length=64)
    mtime: float
    last_ingested_at: datetime | None = None
    status: str = Field(default="new", max_length=32)
    error: str | None = None


class DerivedMemory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    memory_type: str = Field(index=True, max_length=64)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    source_refs: str
    summary_text: str
    qdrant_point_id: str = Field(max_length=64)


class FolderConsent(SQLModel, table=True):
    path: str = Field(primary_key=True, max_length=512)
    granted_at: datetime = Field(default_factory=datetime.utcnow)
