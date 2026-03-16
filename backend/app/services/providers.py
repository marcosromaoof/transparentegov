from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decrypt_secret, encrypt_secret
from app.models import AIModel, AIProviderConfig, AISystemSetting

SUPPORTED_PROVIDERS = ("deepseek", "google", "openai", "openrouter", "groq")


class ProviderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def list_provider_configs(self) -> list[AIProviderConfig]:
        configs = {
            cfg.provider: cfg for cfg in self.db.scalars(select(AIProviderConfig)).all()
        }
        output: list[AIProviderConfig] = []
        for provider in SUPPORTED_PROVIDERS:
            if provider in configs:
                output.append(configs[provider])
            else:
                cfg = AIProviderConfig(provider=provider, enabled=False)
                self.db.add(cfg)
                self.db.flush()
                output.append(cfg)
        self.db.commit()
        return output

    def set_api_key(self, provider: str, api_key: str, enabled: bool) -> AIProviderConfig:
        self._validate_provider(provider)
        config = self._get_provider(provider)
        config.api_key_encrypted = encrypt_secret(api_key)
        config.enabled = enabled
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_models(self, provider: str) -> list[AIModel]:
        self._validate_provider(provider)
        return self.db.scalars(
            select(AIModel).where(AIModel.provider == provider).order_by(AIModel.model_id)
        ).all()

    def sync_models(self, provider: str) -> list[AIModel]:
        self._validate_provider(provider)
        config = self._get_provider(provider)
        if not config.enabled or not config.api_key_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {provider} is not configured",
            )
        api_key = decrypt_secret(config.api_key_encrypted)
        models = self._fetch_remote_models(provider, api_key)

        self.db.query(AIModel).filter(AIModel.provider == provider).delete()
        saved: list[AIModel] = []
        now = datetime.now(timezone.utc)
        for model in models:
            row = AIModel(
                provider=provider,
                model_id=model["model_id"],
                name=model.get("name") or model["model_id"],
                metadata_json=model.get("metadata"),
                is_active=True,
                synced_at=now,
            )
            self.db.add(row)
            saved.append(row)
        config.last_sync_at = now
        self.db.add(config)
        self.db.commit()
        for item in saved:
            self.db.refresh(item)
        return saved

    def get_selected_model(self) -> AISystemSetting:
        setting = self.db.get(AISystemSetting, 1)
        if not setting:
            setting = AISystemSetting(id=1)
            self.db.add(setting)
            self.db.commit()
            self.db.refresh(setting)
        return setting

    def set_selected_model(self, provider: str, model_id: str) -> AISystemSetting:
        self._validate_provider(provider)
        model = self.db.scalar(
            select(AIModel).where(AIModel.provider == provider, AIModel.model_id == model_id)
        )
        if not model:
            raise HTTPException(status_code=404, detail="Model not found. Sync models first.")

        cfg = self._get_provider(provider)
        if not cfg.enabled or not cfg.api_key_encrypted:
            raise HTTPException(status_code=400, detail="Provider is not configured")

        setting = self.get_selected_model()
        setting.selected_provider = provider
        setting.selected_model_id = model_id
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def run_analysis(self, prompt: str) -> tuple[str, str, str]:
        setting = self.get_selected_model()
        if not setting.selected_provider or not setting.selected_model_id:
            raise HTTPException(status_code=400, detail="No model configured")

        provider = setting.selected_provider
        cfg = self._get_provider(provider)
        if not cfg.enabled or not cfg.api_key_encrypted:
            raise HTTPException(status_code=400, detail="Configured provider is disabled")

        api_key = decrypt_secret(cfg.api_key_encrypted)
        answer = self._generate_response(provider, setting.selected_model_id, api_key, prompt)
        return provider, setting.selected_model_id, answer

    def _get_provider(self, provider: str) -> AIProviderConfig:
        row = self.db.scalar(select(AIProviderConfig).where(AIProviderConfig.provider == provider))
        if row:
            return row
        row = AIProviderConfig(provider=provider, enabled=False)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _validate_provider(self, provider: str) -> None:
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=404, detail=f"Unsupported provider: {provider}")

    def _fetch_remote_models(self, provider: str, api_key: str) -> list[dict[str, Any]]:
        settings = self.settings
        if provider == "openai":
            return self._fetch_openai_like(settings.openai_base_url, api_key)
        if provider == "deepseek":
            return self._fetch_openai_like(settings.deepseek_base_url, api_key)
        if provider == "groq":
            return self._fetch_openai_like(settings.groq_base_url, api_key)
        if provider == "openrouter":
            return self._fetch_openrouter(settings.openrouter_base_url, api_key)
        if provider == "google":
            return self._fetch_google(settings.google_base_url, api_key)
        raise HTTPException(status_code=400, detail="Provider not implemented")

    def _fetch_openai_like(self, base_url: str, api_key: str) -> list[dict[str, Any]]:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(f"{base_url}/models", headers={"Authorization": f"Bearer {api_key}"})
        if response.status_code >= 400:
            raise HTTPException(status_code=400, detail=response.text)
        payload = response.json()
        return [
            {
                "model_id": item["id"],
                "name": item.get("id"),
                "metadata": {"owned_by": item.get("owned_by")},
            }
            for item in payload.get("data", [])
            if item.get("id")
        ]

    def _fetch_openrouter(self, base_url: str, api_key: str) -> list[dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://transparentegov.vercel.app",
            "X-Title": "TransparenteGov",
        }
        with httpx.Client(timeout=20.0) as client:
            response = client.get(f"{base_url}/models", headers=headers)
        if response.status_code >= 400:
            raise HTTPException(status_code=400, detail=response.text)
        payload = response.json()
        return [
            {
                "model_id": item["id"],
                "name": item.get("name") or item["id"],
                "metadata": {
                    "context_length": item.get("context_length"),
                    "pricing": item.get("pricing"),
                },
            }
            for item in payload.get("data", [])
            if item.get("id")
        ]

    def _fetch_google(self, base_url: str, api_key: str) -> list[dict[str, Any]]:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(f"{base_url}/models", params={"key": api_key})
        if response.status_code >= 400:
            raise HTTPException(status_code=400, detail=response.text)
        payload = response.json()
        output: list[dict[str, Any]] = []
        for item in payload.get("models", []):
            name = item.get("name", "")
            if not name:
                continue
            model_id = name.split("/")[-1]
            output.append(
                {
                    "model_id": model_id,
                    "name": item.get("displayName") or model_id,
                    "metadata": {
                        "input_token_limit": item.get("inputTokenLimit"),
                        "output_token_limit": item.get("outputTokenLimit"),
                    },
                }
            )
        return output

    def _generate_response(self, provider: str, model_id: str, api_key: str, prompt: str) -> str:
        if provider == "google":
            return self._generate_google(model_id, api_key, prompt)
        return self._generate_openai_like(provider, model_id, api_key, prompt)

    def _generate_openai_like(self, provider: str, model_id: str, api_key: str, prompt: str) -> str:
        settings = self.settings
        base_url = {
            "openai": settings.openai_base_url,
            "deepseek": settings.deepseek_base_url,
            "groq": settings.groq_base_url,
            "openrouter": settings.openrouter_base_url,
        }[provider]
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://transparentegov.vercel.app"
            headers["X-Title"] = "TransparenteGov"

        body = {
            "model": model_id,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é um analista OSINT especializado em investigação de gastos públicos. "
                        "Responda com análise factual, riscos e hipóteses auditáveis."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{base_url}/chat/completions", headers=headers, json=body)
        if response.status_code >= 400:
            raise HTTPException(status_code=400, detail=response.text)
        payload = response.json()
        try:
            return payload["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Invalid provider response: {exc}") from exc

    def _generate_google(self, model_id: str, api_key: str, prompt: str) -> str:
        url = f"{self.settings.google_base_url}/models/{model_id}:generateContent"
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Você é um analista OSINT de gastos públicos. "
                                "Forneça análise objetiva, riscos, padrões e próximos passos investigativos.\n\n"
                                f"{prompt}"
                            )
                        }
                    ]
                }
            ]
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, params={"key": api_key}, json=body)
        if response.status_code >= 400:
            raise HTTPException(status_code=400, detail=response.text)
        payload = response.json()
        try:
            return payload["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Invalid provider response: {exc}") from exc

