from __future__ import annotations

from sqlmodel import Session

from backend.common.config import AuthMode
from backend.common.services.auth.store import ensure_trusted_lan_user
from backend.common.services.auth.types import AuthContext, AuthPrincipal


def resolve_trusted_lan_context(session: Session) -> AuthContext:
    user, identity = ensure_trusted_lan_user(session)
    principal = AuthPrincipal(
        user_id=user.id,
        identity_id=identity.id,
        provider=identity.provider,
        subject=identity.subject,
        auth_mode=AuthMode.TRUSTED_LAN.value,
        transport="trusted_lan",
        user=user,
    )
    return AuthContext(
        principal=principal,
        authenticated=True,
        auth_mode=AuthMode.TRUSTED_LAN.value,
        provider=identity.provider,
        transport="trusted_lan",
    )
