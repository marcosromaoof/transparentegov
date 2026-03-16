from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TransparenteGov OSINT API"
    env: Literal["development", "staging", "production"] = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/transparentegov"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"
    admin_api_key: str = "change-this-admin-key"
    app_encryption_key: str = Field(default="")

    openai_base_url: str = "https://api.openai.com/v1"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    google_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

