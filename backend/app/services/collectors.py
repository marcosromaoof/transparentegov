from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import finish_run, start_run
from app.collectors.registry import COLLECTORS
from app.models import CollectorRun, DatasetSource


def list_sources(db: Session) -> list[DatasetSource]:
    return db.scalars(select(DatasetSource).order_by(DatasetSource.name)).all()


def update_source(
    db: Session,
    source_key: str,
    *,
    frequency: str | None,
    enabled: bool | None,
) -> DatasetSource:
    source = db.scalar(select(DatasetSource).where(DatasetSource.source_key == source_key))
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if frequency is not None:
        source.frequency = frequency
    if enabled is not None:
        source.enabled = enabled
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def run_collector(db: Session, source_key: str) -> CollectorRun:
    source = db.scalar(select(DatasetSource).where(DatasetSource.source_key == source_key))
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if not source.enabled:
        raise HTTPException(status_code=400, detail="Source is disabled")

    collector = COLLECTORS.get(source_key)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector implementation not found")

    _close_stale_runs(db, source)
    run = start_run(db, source)
    try:
        result = collector.run(db)
        run = finish_run(
            db,
            source,
            run,
            status="success",
            fetched=result.fetched,
            saved=result.saved,
        )
    except Exception as exc:  # noqa: BLE001
        run = finish_run(
            db,
            source,
            run,
            status="error",
            fetched=0,
            saved=0,
            error_message=str(exc),
        )
        raise HTTPException(status_code=500, detail=f"Collector failed: {exc}") from exc

    return run


def list_runs(db: Session, source_key: str | None = None) -> list[CollectorRun]:
    stmt = select(CollectorRun).order_by(CollectorRun.started_at.desc()).limit(50)
    if source_key:
        source = db.scalar(select(DatasetSource).where(DatasetSource.source_key == source_key))
        if not source:
            return []
        stmt = stmt.where(CollectorRun.dataset_source_id == source.id)
    return db.scalars(stmt).all()


def _close_stale_runs(db: Session, source: DatasetSource) -> None:
    stale_runs = db.scalars(
        select(CollectorRun).where(
            CollectorRun.dataset_source_id == source.id,
            CollectorRun.status == "running",
            CollectorRun.finished_at.is_(None),
        )
    ).all()
    if not stale_runs:
        return

    now = datetime.now(timezone.utc)
    for stale in stale_runs:
        stale.status = "error"
        stale.finished_at = now
        stale.error_message = "Collector run interrupted before completion"
        stale.records_fetched = stale.records_fetched or 0
        stale.records_saved = stale.records_saved or 0
        db.add(stale)

    source.last_run_at = now
    source.last_status = "error"
    db.add(source)
    db.commit()

