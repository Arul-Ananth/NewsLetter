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
