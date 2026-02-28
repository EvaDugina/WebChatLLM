from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class MessageOut(BaseModel):
    id: int
    role: str = Field(pattern="^(user|assistant)$")
    text: str
    created_at: datetime


class LoginIn(BaseModel):
    access_key: str


class LoginOut(BaseModel):
    token: str
    expires_in: int


class SendMessageIn(BaseModel):
    text: str


class SendMessageOut(BaseModel):
    user: MessageOut
    assistant: MessageOut

