from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.security import TokenService, validate_access_key_format
from app.models.message import LoginIn, LoginOut

from .deps import get_token_service, require_auth


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, token_service: TokenService = Depends(get_token_service)) -> LoginOut:
    key = payload.access_key or ""
    if not validate_access_key_format(key):
        raise HTTPException(status_code=400, detail="invalid_key_format")
    if key != settings.access_key:
        raise HTTPException(status_code=401, detail="wrong_key")
    token = token_service.issue(sub="access")
    return LoginOut(token=token, expires_in=settings.token_ttl_seconds)


@router.get("/validate")
def validate(_: object = Depends(require_auth)) -> dict:
    return {"ok": True}

