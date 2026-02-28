from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from app.core.config import settings
from app.core.security import TokenPayload, TokenService


_token_service = TokenService(secret=settings.token_secret)


def get_token_service() -> TokenService:
    return _token_service


def require_auth(
    authorization: str | None = Header(default=None, alias="Authorization"),
    token_service: TokenService = Depends(get_token_service),
) -> TokenPayload:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return token_service.verify(token, max_age_seconds=settings.token_ttl_seconds)
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid_token")

