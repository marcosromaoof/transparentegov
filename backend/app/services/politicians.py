from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    City,
    Contract,
    ParliamentaryAmendment,
    Politician,
    PublicAgency,
    PublicSpending,
    State,
)


def list_positions(db: Session) -> list[str]:
    rows = db.scalars(select(Politician.position).distinct().order_by(Politician.position.asc())).all()
    return [row for row in rows if row]


def list_politicians(
    db: Session,
    *,
    name: str | None,
    position: str | None,
    state_id: int | None,
    city_id: int | None,
    active_only: bool,
    limit: int,
) -> list[Politician]:
    stmt = select(Politician)
    if name:
        stmt = stmt.where(Politician.name.ilike(f"%{name}%"))
    if position:
        stmt = stmt.where(Politician.position == position)
    if state_id:
        stmt = stmt.where(Politician.state_id == state_id)
    if city_id:
        stmt = stmt.where(Politician.city_id == city_id)

    if active_only:
        today = date.today()
        stmt = stmt.where(
            (Politician.start_term.is_(None)) | (Politician.start_term <= today),
            (Politician.end_term.is_(None)) | (Politician.end_term >= today),
        )

    stmt = stmt.order_by(Politician.name.asc()).limit(min(max(limit, 1), 200))
    return db.scalars(stmt).all()


def get_politician_profile(db: Session, politician_id: int) -> dict:
    politician = db.get(Politician, politician_id)
    if not politician:
        raise HTTPException(status_code=404, detail="Politician not found")

    state = db.get(State, politician.state_id) if politician.state_id else None
    city = db.get(City, politician.city_id) if politician.city_id else None

    agency_ids: list[int] = []
    if politician.city_id:
        agency_ids = db.scalars(
            select(PublicAgency.id).where(PublicAgency.city_id == politician.city_id)
        ).all()
    elif politician.state_id:
        agency_ids = db.scalars(
            select(PublicAgency.id)
            .join(City, City.id == PublicAgency.city_id)
            .where(City.state_id == politician.state_id)
        ).all()

    contracts = []
    spending = []
    if agency_ids:
        contracts = db.scalars(
            select(Contract)
            .where(Contract.agency_id.in_(agency_ids))
            .order_by(Contract.start_date.desc().nullslast(), Contract.id.desc())
            .limit(200)
        ).all()
        spending = db.scalars(
            select(PublicSpending)
            .where(PublicSpending.agency_id.in_(agency_ids))
            .order_by(PublicSpending.year.desc(), PublicSpending.month.desc(), PublicSpending.id.desc())
            .limit(200)
        ).all()

    amendments = db.scalars(
        select(ParliamentaryAmendment)
        .where(ParliamentaryAmendment.politician_id == politician.id)
        .order_by(ParliamentaryAmendment.year.desc(), ParliamentaryAmendment.id.desc())
        .limit(200)
    ).all()

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
    total_amendments = db.scalar(
        select(func.coalesce(func.sum(ParliamentaryAmendment.value), 0)).where(
            ParliamentaryAmendment.politician_id == politician.id
        )
    )

    return {
        "politician": politician,
        "state": state,
        "city": city,
        "contracts": contracts,
        "spending": spending,
        "amendments": amendments,
        "totals": {
            "contracts": total_contracts or Decimal("0"),
            "spending": total_spending or Decimal("0"),
            "amendments": total_amendments or Decimal("0"),
        },
    }

