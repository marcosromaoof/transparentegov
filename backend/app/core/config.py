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

    portal_transparencia_base_url: str = "https://api.portaldatransparencia.gov.br"
    portal_transparencia_api_key: str | None = None
    portal_emendas_years_back: int = 2
    portal_emendas_max_pages_per_year: int = 15

    pncp_base_url: str = "https://pncp.gov.br/api/consulta/v1"
    pncp_days_back: int = 120
    pncp_max_pages: int = 30
    pncp_page_size: int = 50
    pncp_backfill_days: int = 365
    pncp_backfill_max_pages: int = 120
    pncp_backfill_min_cities: int = 200
    pncp_max_runtime_seconds: int = 240

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

