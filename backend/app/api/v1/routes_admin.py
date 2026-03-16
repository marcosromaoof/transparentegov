from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AdminActor, DBSession
from app.schemas.api import (
    AIModelOut,
    AIProviderKeyUpdate,
    AIProviderOut,
    AISelectionOut,
    AISelectionUpdate,
    DatasetSourceOut,
    DatasetSourceUpdate,
)
from app.services.audit import log_audit
from app.services.collectors import list_sources, update_source
from app.services.providers import ProviderService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/providers", response_model=list[AIProviderOut])
def providers(db: DBSession, actor: AdminActor) -> list[AIProviderOut]:
    service = ProviderService(db)
    rows = service.list_provider_configs()
    log_audit(db, actor=actor, action="read", resource="ai_provider_configs")
    return [
        AIProviderOut(
            provider=row.provider,
            enabled=row.enabled,
            configured=bool(row.api_key_encrypted),
            last_sync_at=row.last_sync_at,
        )
        for row in rows
    ]


@router.put("/providers/{provider}", response_model=AIProviderOut)
def provider_update(
    provider: str,
    payload: AIProviderKeyUpdate,
    db: DBSession,
    actor: AdminActor,
) -> AIProviderOut:
    service = ProviderService(db)
    row = service.set_api_key(provider, payload.api_key, payload.enabled)
    log_audit(db, actor=actor, action="update", resource="ai_provider", resource_id=provider)
    return AIProviderOut(
        provider=row.provider,
        enabled=row.enabled,
        configured=bool(row.api_key_encrypted),
        last_sync_at=row.last_sync_at,
    )


@router.post("/providers/{provider}/sync-models", response_model=list[AIModelOut])
def provider_sync_models(provider: str, db: DBSession, actor: AdminActor) -> list[AIModelOut]:
    service = ProviderService(db)
    rows = service.sync_models(provider)
    log_audit(db, actor=actor, action="sync_models", resource="ai_provider", resource_id=provider)
    return [AIModelOut.model_validate(item) for item in rows]


@router.get("/providers/{provider}/models", response_model=list[AIModelOut])
def provider_models(provider: str, db: DBSession, actor: AdminActor) -> list[AIModelOut]:
    service = ProviderService(db)
    rows = service.get_models(provider)
    return [AIModelOut.model_validate(item) for item in rows]


@router.get("/model-selection", response_model=AISelectionOut)
def get_selection(db: DBSession, actor: AdminActor) -> AISelectionOut:
    service = ProviderService(db)
    row = service.get_selected_model()
    return AISelectionOut(provider=row.selected_provider, model_id=row.selected_model_id)


@router.put("/model-selection", response_model=AISelectionOut)
def set_selection(payload: AISelectionUpdate, db: DBSession, actor: AdminActor) -> AISelectionOut:
    service = ProviderService(db)
    row = service.set_selected_model(payload.provider, payload.model_id)
    log_audit(
        db,
        actor=actor,
        action="set_model",
        resource="ai_system_settings",
        metadata={"provider": payload.provider, "model_id": payload.model_id},
    )
    return AISelectionOut(provider=row.selected_provider, model_id=row.selected_model_id)


@router.get("/datasets", response_model=list[DatasetSourceOut])
def datasets(db: DBSession, actor: AdminActor) -> list[DatasetSourceOut]:
    rows = list_sources(db)
    return [DatasetSourceOut.model_validate(item) for item in rows]


@router.patch("/datasets/{source_key}", response_model=DatasetSourceOut)
def dataset_update(
    source_key: str,
    payload: DatasetSourceUpdate,
    db: DBSession,
    actor: AdminActor,
) -> DatasetSourceOut:
    row = update_source(db, source_key, frequency=payload.frequency, enabled=payload.enabled)
    log_audit(db, actor=actor, action="update", resource="dataset_source", resource_id=source_key)
    return DatasetSourceOut.model_validate(row)

