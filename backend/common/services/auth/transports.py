from __future__ import annotations

from fastapi import Request

AUTHORIZATION_PREFIX = "Bearer "


def extract_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith(AUTHORIZATION_PREFIX):
        return None
    token = authorization[len(AUTHORIZATION_PREFIX) :].strip()
    return token or None
