from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict:
    return {
        "status": "ok",
        "service": "transparentegov-osint-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

