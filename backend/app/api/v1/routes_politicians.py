from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSession
from app.schemas.api import PoliticianOut, PoliticianProfileOut
from app.services.politicians import get_politician_profile, list_politicians, list_positions

router = APIRouter(prefix="/politicians", tags=["politicians"])


@router.get("/positions", response_model=list[str])
def positions(db: DBSession) -> list[str]:
    return list_positions(db)


@router.get("", response_model=list[PoliticianOut])
def politicians(
    db: DBSession,
    name: str | None = Query(default=None),
    position: str | None = Query(default=None),
    state_id: int | None = Query(default=None),
    city_id: int | None = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[PoliticianOut]:
    rows = list_politicians(
        db,
        name=name,
        position=position,
        state_id=state_id,
        city_id=city_id,
        active_only=active_only,
        limit=limit,
    )
    return [PoliticianOut.model_validate(row) for row in rows]


@router.get("/{politician_id}/profile", response_model=PoliticianProfileOut)
def profile(politician_id: int, db: DBSession) -> PoliticianProfileOut:
    payload = get_politician_profile(db, politician_id)
    return PoliticianProfileOut(
        politician=PoliticianOut.model_validate(payload["politician"]),
        state=payload["state"],
        city=payload["city"],
        contracts=payload["contracts"],
        spending=payload["spending"],
        amendments=payload["amendments"],
        totals=payload["totals"],
    )

