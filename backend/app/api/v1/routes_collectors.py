from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import AdminActor, DBSession
from app.schemas.api import CollectorRunOut
from app.services.audit import log_audit
from app.services.collectors import list_runs, run_collector

router = APIRouter(prefix="/collectors", tags=["collectors"])


@router.post("/run/{source_key}", response_model=CollectorRunOut)
def run(source_key: str, db: DBSession, actor: AdminActor) -> CollectorRunOut:
    row = run_collector(db, source_key)
    log_audit(db, actor=actor, action="run", resource="collector", resource_id=source_key)
    return CollectorRunOut.model_validate(row)


@router.get("/runs", response_model=list[CollectorRunOut])
def runs(
    db: DBSession,
    actor: AdminActor,
    source_key: str | None = Query(default=None),
) -> list[CollectorRunOut]:
    rows = list_runs(db, source_key)
    return [CollectorRunOut.model_validate(item) for item in rows]

