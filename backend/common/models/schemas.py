from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class UserSignup(StrictBaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=255)


class UserLogin(StrictBaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)


class AuthStatus(StrictBaseModel):
    message: str
    user_id: int | None = None
    trusted_lan_mode: bool = False
    auth_mode: str
    authenticated: bool = False
    provider: str | None = None
    requires_login: bool = True
    session_token: str | None = None


class SignupResponse(StrictBaseModel):
    message: str
    user_id: int
    auth_provider: str


class BillingReceipt(StrictBaseModel):
    deducted: int
    remaining: int | str


class NewsRequest(StrictBaseModel):
    topic: str = Field(min_length=1, max_length=255)
    serper_api_key: str | None = None
    openai_api_key: str | None = None


class NewsResponse(StrictBaseModel):
    topic: str
    content: str
    bill: BillingReceipt


class FeedbackRequest(StrictBaseModel):
    original_topic: str = Field(min_length=1, max_length=255)
    feedback_text: str = Field(min_length=1, max_length=2000)
    sentiment: str = Field(min_length=1, max_length=50)


class FeedbackResponse(StrictBaseModel):
    status: str


class MessageResponse(StrictBaseModel):
    message: str


class MemoryRecord(StrictBaseModel):
    id: str
    document: str
    metadata: dict[str, Any]


class ProfileResponse(StrictBaseModel):
    memories: list[MemoryRecord]
