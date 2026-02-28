from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Final

import json
import time
from pathlib import Path

import requests

from app.services.llm.base import ChatLLM


class OpenRouterChatService(ChatLLM):
    def __init__(self, api_key: str, model: str, system_prompt: str) -> None:
        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt

    def generate_reply(self, user_text: str) -> str:
        # Для совместимости используем нестрогий доступ к полям ответа.
        prompt = f"{self._system_prompt}\n\nUser: {user_text}\nAssistant:"

        payload = {
            "model": self._model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }

        # region agent log
        _append_debug_log(
            hypothesis_id="H1",
            location="openrouter_client.py:generate_reply:before_request",
            message="Sending OpenRouter request",
            data={"model": self._model, "prompt_length": len(prompt)},
        )
        # endregion

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps(payload),
                timeout=30,
            )
        except Exception as exc:  # noqa: BLE001
            _append_debug_log(
                hypothesis_id="H1",
                location="openrouter_client.py:generate_reply:request_error",
                message="Error calling OpenRouter",
                data={"error_type": type(exc).__name__},
            )
            raise RuntimeError("openrouter_request_failed") from exc

        if resp.status_code >= 400:
            _append_debug_log(
                hypothesis_id="H1",
                location="openrouter_client.py:generate_reply:http_error",
                message="OpenRouter HTTP error",
                data={"status_code": resp.status_code},
            )
            raise RuntimeError(f"openrouter_http_{resp.status_code}")

        body: Any
        try:
            body = resp.json()
        except Exception as exc:  # noqa: BLE001
            _append_debug_log(
                hypothesis_id="H1",
                location="openrouter_client.py:generate_reply:json_error",
                message="Failed to decode OpenRouter JSON",
                data={"error_type": type(exc).__name__},
            )
            raise RuntimeError("openrouter_invalid_json") from exc

        # Попытка достать текст из ответа в формате, совместимом с OpenAI/OpenRouter.
        content: str | None = _extract_content(body)
        if not content or not content.strip():
            raise RuntimeError("empty_model_response")
        return content.strip()


def _extract_content(res: Any) -> str | None:
    """
    Универсально извлекает текст ответа из объекта SDK/словаря.

    Ожидаемый формат совместим с OpenAI:
      res.choices[0].message.content

    При этом content может быть как строкой, так и массивом "частей"
    (list[ContentPart]), поэтому обрабатываем оба варианта.
    """

    choices: Any = getattr(res, "choices", None)
    if isinstance(choices, Iterable):
        choices_list = list(choices)
        if not choices_list:
            return None
        first = choices_list[0]
        message = getattr(first, "message", None)
        if isinstance(first, dict):
            message = first.get("message", message)
        if isinstance(message, dict):
            content = message.get("content")
        else:
            content = getattr(message, "content", None)
        text = _content_to_str(content)
        if text is not None:
            return text

    # Fallback: вдруг сам объект похож на словарь с expected структурой
    if isinstance(res, dict):
        ch = res.get("choices") or []
        if isinstance(ch, list) and ch:
            msg = ch[0].get("message") or {}
            content = msg.get("content")
            text = _content_to_str(content)
            if text is not None:
                return text

    return None


_DEBUG_LOG_PATH: Final[Path] = Path("debug-ec1dc5.log")


def _append_debug_log(
    *,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> None:
    """
    Пишет одну строку NDJSON в debug-ec1dc5.log для отладки.

    Не логируем секреты (API-ключ, токены, сырой текст ответа).
    """

    payload = {
        "sessionId": "ec1dc5",
        "runId": "run1",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }

    try:
        with _DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # Отладка не должна ломать основной поток.
        pass


def _content_to_str(content: Any) -> str | None:
    """
    Преобразует поле content, которое может быть строкой или списком "частей",
    в единую текстовую строку.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            text_value: Any = None
            if isinstance(part, dict):
                text_value = part.get("text")
            else:
                text_value = getattr(part, "text", None)
            if isinstance(text_value, str):
                parts.append(text_value)
        if parts:
            return "".join(parts)

    return None


