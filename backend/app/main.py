from __future__ import annotations

from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_chat import get_storage, router as chat_router


app = FastAPI(title="ChatGemini API", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    # Инициализируем БД при старте.
    storage = get_storage()
    storage.init()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

