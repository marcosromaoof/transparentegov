from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSession
from app.schemas.api import CityOut, CityProfileOut, CountryOut, StateOut
from app.services.territory import get_city_profile, list_cities, list_countries, list_states

router = APIRouter(prefix="/territory", tags=["territory"])


@router.get("/countries", response_model=list[CountryOut])
def get_countries(db: DBSession) -> list[CountryOut]:
    return [CountryOut.model_validate(item) for item in list_countries(db)]


@router.get("/states", response_model=list[StateOut])
def get_states(
    db: DBSession,
    country_id: int | None = Query(default=None),
) -> list[StateOut]:
    return [StateOut.model_validate(item) for item in list_states(db, country_id)]


@router.get("/cities", response_model=list[CityOut])
def get_cities(
    db: DBSession,
    state_id: int | None = Query(default=None),
    query: str | None = Query(default=None),
) -> list[CityOut]:
    return [CityOut.model_validate(item) for item in list_cities(db, state_id, query)]


@router.get("/cities/{city_id}/profile", response_model=CityProfileOut)
def city_profile(city_id: int, db: DBSession) -> CityProfileOut:
    payload = get_city_profile(db, city_id)
    return CityProfileOut(
        city=CityOut.model_validate(payload["city"]),
        country=CountryOut.model_validate(payload["country"]),
        state=StateOut.model_validate(payload["state"]),
        public_agencies=payload["public_agencies"],
        hospitals=payload["hospitals"],
        schools=payload["schools"],
        police_units=payload["police_units"],
        politicians=payload["politicians"],
        contracts=payload["contracts"],
        spending=payload["spending"],
        amendments=payload["amendments"],
        revenues=payload["revenues"],
        totals=payload["totals"],
    )

