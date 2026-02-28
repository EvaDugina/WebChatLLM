from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.models.message import MessageOut, SendMessageIn, SendMessageOut
from app.services.llm.base import ChatLLM
from app.services.llm.gemini import GeminiChatService
from app.services.llm.openrouter_client import OpenRouterChatService
from app.services.storage.sqlite import SqliteStorage

from .deps import require_auth


router = APIRouter(prefix="", tags=["chat"])


def get_storage() -> SqliteStorage:
    return SqliteStorage(db_path=settings.db_path)


def get_llm() -> ChatLLM:
    provider = (settings.llm_provider or "gemini").lower()
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise HTTPException(status_code=500, detail="gemini_api_key_not_configured")
        return GeminiChatService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            system_prompt=settings.system_prompt,
        )
    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise HTTPException(status_code=500, detail="openrouter_api_key_not_configured")
        return OpenRouterChatService(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            system_prompt=settings.system_prompt,
        )
    raise HTTPException(status_code=500, detail="unsupported_llm_provider")


@router.get("/messages", response_model=list[MessageOut])
def list_messages(
    _: object = Depends(require_auth),
    storage: SqliteStorage = Depends(get_storage),
) -> list[MessageOut]:
    return [
        MessageOut(id=m.id, role=m.role, text=m.text, created_at=m.created_at)
        for m in storage.list_messages()
    ]


@router.post("/messages", response_model=SendMessageOut)
def send_message(
    payload: SendMessageIn,
    _: object = Depends(require_auth),
    storage: SqliteStorage = Depends(get_storage),
    llm: ChatLLM = Depends(get_llm),
) -> SendMessageOut:
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty_message")
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="message_too_long")

    user_msg = storage.add_message(role="user", text=text)
    try:
        reply = llm.generate_reply(user_text=text)
    except Exception:
        raise HTTPException(status_code=502, detail="llm_request_failed")
    assistant_msg = storage.add_message(role="assistant", text=reply)

    return SendMessageOut(
        user=MessageOut(id=user_msg.id, role=user_msg.role, text=user_msg.text, created_at=user_msg.created_at),
        assistant=MessageOut(
            id=assistant_msg.id,
            role=assistant_msg.role,
            text=assistant_msg.text,
            created_at=assistant_msg.created_at,
        ),
    )

