from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from backend.common.config import AuthMode, settings
from backend.common.database import get_session
from backend.common.models.schemas import AuthStatus, MessageResponse, SignupResponse, UserLogin, UserSignup
from backend.common.services.auth.providers.interactive import login as interactive_login
from backend.common.services.auth.providers.interactive import signup as interactive_signup
from backend.common.services.auth.resolver import get_auth_context
from backend.common.services.auth.store import revoke_session_token
from backend.common.services.auth.transports import extract_bearer_token
from backend.common.services.auth.types import AuthContext

router = APIRouter(tags=["Auth"])


def _status_from_context(
    auth_context: AuthContext,
    *,
    message: str,
    session_token: str | None = None,
) -> AuthStatus:
    principal = auth_context.principal
    return AuthStatus(
        message=message,
        user_id=principal.user_id if principal else None,
        trusted_lan_mode=auth_context.auth_mode == AuthMode.TRUSTED_LAN.value,
        auth_mode=auth_context.auth_mode,
        authenticated=auth_context.authenticated,
        provider=auth_context.provider,
        requires_login=auth_context.auth_mode != AuthMode.TRUSTED_LAN.value,
        session_token=session_token,
    )


@router.get("/status", response_model=AuthStatus)
def get_status(auth_context: AuthContext = Depends(get_auth_context)):
    if auth_context.auth_mode == AuthMode.TRUSTED_LAN.value:
        return _status_from_context(
            auth_context,
            message="Trusted LAN mode is active.",
        )
    if auth_context.authenticated:
        return _status_from_context(auth_context, message="Authenticated session restored.")
    return _status_from_context(auth_context, message="Authentication required.")


@router.post("/signup", status_code=201, response_model=SignupResponse)
def signup(user_data: UserSignup, session: Session = Depends(get_session)):
    try:
        user, identity = interactive_signup(session, user_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SignupResponse(
        message="User created",
        user_id=user.id,
        auth_provider=identity.provider,
    )


@router.post("/login", response_model=AuthStatus)
def login(
    user_data: UserLogin,
    auth_context: AuthContext = Depends(get_auth_context),
    session: Session = Depends(get_session),
):
    if settings.auth_mode() == AuthMode.TRUSTED_LAN:
        return _status_from_context(
            auth_context,
            message="Trusted LAN mode is enabled. Browser login is not required.",
        )

    try:
        login_context, raw_token = interactive_login(session, user_data)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return _status_from_context(
        login_context,
        message="Credentials verified.",
        session_token=raw_token,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    session: Session = Depends(get_session),
):
    if settings.auth_mode() == AuthMode.INTERACTIVE:
        token = extract_bearer_token(request)
        if token:
            revoke_session_token(session, token)
    return MessageResponse(message="Signed out")
