from __future__ import annotations

from decimal import Decimal
import unicodedata

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    City,
    Contract,
    Country,
    Hospital,
    MunicipalRevenue,
    ParliamentaryAmendment,
    PoliceUnit,
    Politician,
    PublicAgency,
    PublicSpending,
    School,
    State,
)


def list_countries(db: Session) -> list[Country]:
    return db.scalars(select(Country).order_by(Country.name)).all()


def list_states(db: Session, country_id: int | None) -> list[State]:
    stmt = select(State)
    if country_id:
        stmt = stmt.where(State.country_id == country_id)
    return db.scalars(stmt.order_by(State.name)).all()


def list_cities(db: Session, state_id: int | None, query: str | None) -> list[City]:
    stmt = select(City)
    if state_id:
        stmt = stmt.where(City.state_id == state_id)
    rows = db.scalars(stmt.order_by(City.name)).all()
    if not query:
        return rows

    needle = _normalize(query)
    return [row for row in rows if needle in _normalize(row.name)]


def get_city_profile(db: Session, city_id: int) -> dict:
    city = db.get(City, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    state = db.get(State, city.state_id)
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    country = db.get(Country, state.country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    agencies = db.scalars(select(PublicAgency).where(PublicAgency.city_id == city_id)).all()
    hospitals = db.scalars(select(Hospital).where(Hospital.city_id == city_id)).all()
    schools = db.scalars(select(School).where(School.city_id == city_id)).all()
    police_units = db.scalars(select(PoliceUnit).where(PoliceUnit.city_id == city_id)).all()
    politicians = db.scalars(
        select(Politician).where((Politician.city_id == city_id) | (Politician.state_id == state.id))
    ).all()

    agency_ids = [a.id for a in agencies]
    contracts = (
        db.scalars(select(Contract).where(Contract.agency_id.in_(agency_ids))).all() if agency_ids else []
    )
    spending = (
        db.scalars(select(PublicSpending).where(PublicSpending.agency_id.in_(agency_ids))).all()
        if agency_ids
        else []
    )
    amendments = db.scalars(
        select(ParliamentaryAmendment).where(ParliamentaryAmendment.city_id == city_id)
    ).all()
    revenues = db.scalars(select(MunicipalRevenue).where(MunicipalRevenue.city_id == city_id)).all()

    total_contracts = (
        db.scalar(select(func.coalesce(func.sum(Contract.value), 0)).where(Contract.agency_id.in_(agency_ids)))
        if agency_ids
        else Decimal("0")
    )
    total_spending = (
        db.scalar(
            select(func.coalesce(func.sum(PublicSpending.value), 0)).where(
                PublicSpending.agency_id.in_(agency_ids)
            )
        )
        if agency_ids
        else Decimal("0")
    )
    total_revenue = db.scalar(
        select(func.coalesce(func.sum(MunicipalRevenue.value), 0)).where(MunicipalRevenue.city_id == city_id)
    )
    total_amendments = db.scalar(
        select(func.coalesce(func.sum(ParliamentaryAmendment.value), 0)).where(
            ParliamentaryAmendment.city_id == city_id
        )
    )

    return {
        "city": city,
        "state": state,
        "country": country,
        "public_agencies": agencies,
        "hospitals": hospitals,
        "schools": schools,
        "police_units": police_units,
        "politicians": politicians,
        "contracts": contracts,
        "spending": spending,
        "amendments": amendments,
        "revenues": revenues,
        "totals": {
            "contracts": total_contracts or Decimal("0"),
            "spending": total_spending or Decimal("0"),
            "revenues": total_revenue or Decimal("0"),
            "amendments": total_amendments or Decimal("0"),
        },
    }


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return without_accents.lower().strip()

