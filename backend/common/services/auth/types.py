from __future__ import annotations

from dataclasses import dataclass

from backend.common.models.sql import User


@dataclass(slots=True)
class AuthPrincipal:
    user_id: int
    identity_id: int
    provider: str
    subject: str
    auth_mode: str
    transport: str
    user: User


@dataclass(slots=True)
class AuthContext:
    principal: AuthPrincipal | None
    authenticated: bool
    auth_mode: str
    provider: str | None
    transport: str | None
