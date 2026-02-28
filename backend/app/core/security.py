from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer


ACCESS_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{8,255}$")


def validate_access_key_format(value: str) -> bool:
    return bool(ACCESS_KEY_RE.fullmatch(value or ""))


@dataclass(frozen=True)
class TokenPayload:
    sub: str


class TokenService:
    def __init__(self, secret: str, salt: str = "chatgemini-token") -> None:
        self._serializer = URLSafeTimedSerializer(secret_key=secret, salt=salt)

    def issue(self, sub: str) -> str:
        return self._serializer.dumps({"sub": sub})

    def verify(self, token: str, max_age_seconds: int) -> TokenPayload:
        try:
            data: Any = self._serializer.loads(token, max_age=max_age_seconds)
        except (BadSignature, BadTimeSignature) as e:
            raise ValueError("invalid_token") from e
        sub = data.get("sub")
        if not isinstance(sub, str) or not sub:
            raise ValueError("invalid_token")
        return TokenPayload(sub=sub)

