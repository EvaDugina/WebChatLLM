from __future__ import annotations

from abc import ABC, abstractmethod


class ChatLLM(ABC):
    @abstractmethod
    def generate_reply(self, user_text: str) -> str:  # pragma: no cover - interface
        ...

