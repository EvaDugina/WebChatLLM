from __future__ import annotations

from google import genai

from app.services.llm.base import ChatLLM


class GeminiChatService(ChatLLM):
    def __init__(self, api_key: str, model: str, system_prompt: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._system_prompt = system_prompt

    def generate_reply(self, user_text: str) -> str:
        # Контекст диалога не обязателен по ТЗ — используем только system + текущее сообщение.
        contents = f"{self._system_prompt}\n\nUser: {user_text}\nAssistant:"
        resp = self._client.models.generate_content(model=self._model, contents=contents)
        text = getattr(resp, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("empty_model_response")
        return text.strip()

