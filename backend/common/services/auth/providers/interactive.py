from __future__ import annotations

from sqlmodel import Session

from backend.common.config import AuthMode
from backend.common.models.schemas import UserLogin, UserSignup
from backend.common.models.sql import User
from backend.common.services.auth.auth_utils import verify_password
from backend.common.services.auth.store import (
    INTERACTIVE_PROVIDER,
    SESSION_TRANSPORT,
    create_session_token,
    create_user_with_password_identity,
    get_identity_by_email,
    resolve_session_token,
)
from backend.common.services.auth.types import AuthContext, AuthPrincipal


def signup(session: Session, user_data: UserSignup):
    return create_user_with_password_identity(
        session,
        full_name=user_data.full_name,
        email=user_data.email,
        password=user_data.password,
    )


def login(session: Session, user_data: UserLogin) -> tuple[AuthContext, str]:
    identity = get_identity_by_email(session, INTERACTIVE_PROVIDER, user_data.email)
    if identity is None or not identity.password_hash:
        raise ValueError("Invalid credentials")
    if not verify_password(user_data.password, identity.password_hash):
        raise ValueError("Invalid credentials")

    user = session.get(User, identity.user_id)
    if user is None:
        raise ValueError("Invalid credentials")

    raw_token = create_session_token(session, user=user, identity=identity)
    principal = AuthPrincipal(
        user_id=user.id,
        identity_id=identity.id,
        provider=identity.provider,
        subject=identity.subject,
        auth_mode=AuthMode.INTERACTIVE.value,
        transport=SESSION_TRANSPORT,
        user=user,
    )
    return (
        AuthContext(
            principal=principal,
            authenticated=True,
            auth_mode=AuthMode.INTERACTIVE.value,
            provider=identity.provider,
            transport=SESSION_TRANSPORT,
        ),
        raw_token,
    )


def resolve_interactive_context(session: Session, raw_token: str | None) -> AuthContext:
    if not raw_token:
        return AuthContext(
            principal=None,
            authenticated=False,
            auth_mode=AuthMode.INTERACTIVE.value,
            provider=None,
            transport=SESSION_TRANSPORT,
        )

    resolved = resolve_session_token(session, raw_token)
    if resolved is None:
        return AuthContext(
            principal=None,
            authenticated=False,
            auth_mode=AuthMode.INTERACTIVE.value,
            provider=None,
            transport=SESSION_TRANSPORT,
        )

    _auth_session, identity, user = resolved
    principal = AuthPrincipal(
        user_id=user.id,
        identity_id=identity.id,
        provider=identity.provider,
        subject=identity.subject,
        auth_mode=AuthMode.INTERACTIVE.value,
        transport=SESSION_TRANSPORT,
        user=user,
    )
    return AuthContext(
        principal=principal,
        authenticated=True,
        auth_mode=AuthMode.INTERACTIVE.value,
        provider=identity.provider,
        transport=SESSION_TRANSPORT,
    )
