from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = Field(default="dev", validation_alias="APP_ENV")

    # Авторизация
    access_key: str = Field(validation_alias="ACCESS_KEY")
    token_secret: str = Field(validation_alias="TOKEN_SECRET")
    token_ttl_seconds: int = Field(default=60 * 60 * 24, validation_alias="TOKEN_TTL_SECONDS")

    # LLM / тема чата
    llm_provider: str = Field(default="gemini", validation_alias="LLM_PROVIDER")
    system_prompt: str = Field(
        default=(
        "You are a helpful assistant for a themed chat about cooking. "
        "Answer concisely and safely."
        ),
        validation_alias="SYSTEM_PROMPT",
    )

    # Gemini
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", validation_alias="GEMINI_MODEL")

    # OpenRouter
    openrouter_api_key: str | None = Field(default=None, validation_alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="openai/gpt-4.1-mini",
        validation_alias="OPENROUTER_MODEL",
    )

    db_path: str = Field(default="/data/chat.db", validation_alias="DB_PATH")


settings = Settings()

