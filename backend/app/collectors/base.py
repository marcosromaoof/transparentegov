from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy.orm import Session

from app.models import CollectorRun, DatasetSource


@dataclass
class CollectorResult:
    fetched: int
    saved: int


class Collector(Protocol):
    source_key: str

    def run(self, db: Session) -> CollectorResult:
        ...


def start_run(db: Session, source: DatasetSource) -> CollectorRun:
    run = CollectorRun(dataset_source_id=source.id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finish_run(
    db: Session,
    source: DatasetSource,
    run: CollectorRun,
    *,
    status: str,
    fetched: int,
    saved: int,
    error_message: str | None = None,
) -> CollectorRun:
    run.status = status
    run.records_fetched = fetched
    run.records_saved = saved
    run.finished_at = datetime.now(timezone.utc)
    run.error_message = error_message
    source.last_run_at = run.finished_at
    source.last_status = status
    db.add_all([run, source])
    db.commit()
    db.refresh(run)
    return run

