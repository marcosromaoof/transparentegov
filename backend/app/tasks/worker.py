from __future__ import annotations

from celery import Celery
from sqlalchemy import select

from app.collectors.registry import COLLECTORS
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import DatasetSource

settings = get_settings()
celery_app = Celery("transparentegov", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    beat_schedule={
        "run-camara-hourly": {
            "task": "app.tasks.worker.run_collector_task",
            "schedule": 3600,
            "args": ("camara",),
        },
        "run-ibge-daily": {
            "task": "app.tasks.worker.run_collector_task",
            "schedule": 86400,
            "args": ("ibge",),
        },
    },
)


@celery_app.task(name="app.tasks.worker.run_collector_task")
def run_collector_task(source_key: str) -> dict:
    collector = COLLECTORS.get(source_key)
    if not collector:
        return {"status": "error", "reason": "collector_not_found"}

    with SessionLocal() as db:
        source = db.scalar(select(DatasetSource).where(DatasetSource.source_key == source_key))
        if not source or not source.enabled:
            return {"status": "skipped", "reason": "source_disabled_or_missing"}
        result = collector.run(db)
        return {"status": "success", "fetched": result.fetched, "saved": result.saved}

