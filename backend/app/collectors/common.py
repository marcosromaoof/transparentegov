from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import City, Politician, State


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = re.sub(r"\s+", " ", without_accents).strip().lower()
    return cleaned


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def parse_decimal_value(value: str | int | float | Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    text = str(value).strip()
    if not text:
        return Decimal("0")

    # Supporta formatos "1.234,56" e "1234.56"
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def politician_key(
    *,
    name: str,
    position: str,
    state_id: int | None,
    city_id: int | None,
) -> tuple[str, str, int | None, int | None]:
    return (normalize_text(name), normalize_text(position), state_id, city_id)


def load_states_by_code(db: Session) -> dict[str, State]:
    rows = db.scalars(select(State)).all()
    return {row.code.upper(): row for row in rows}


def load_city_indexes(
    db: Session,
) -> tuple[dict[tuple[int, str], City], dict[str, City]]:
    rows = db.scalars(select(City)).all()
    by_state_name: dict[tuple[int, str], City] = {}
    by_ibge_code: dict[str, City] = {}
    for row in rows:
        by_state_name[(row.state_id, normalize_text(row.name))] = row
        if row.ibge_code:
            by_ibge_code[str(row.ibge_code)] = row
    return by_state_name, by_ibge_code


def load_politician_cache(
    db: Session,
) -> dict[tuple[str, str, int | None, int | None], Politician]:
    rows = db.scalars(select(Politician)).all()
    return {
        politician_key(
            name=row.name,
            position=row.position,
            state_id=row.state_id,
            city_id=row.city_id,
        ): row
        for row in rows
    }


def upsert_politician(
    db: Session,
    cache: dict[tuple[str, str, int | None, int | None], Politician],
    *,
    name: str,
    party: str | None,
    position: str,
    state_id: int | None,
    city_id: int | None,
    start_term: date | None,
    end_term: date | None,
) -> bool:
    key = politician_key(name=name, position=position, state_id=state_id, city_id=city_id)
    row = cache.get(key)
    if row:
        changed = False
        if party and row.party != party:
            row.party = party
            changed = True
        if start_term and row.start_term != start_term:
            row.start_term = start_term
            changed = True
        if end_term and row.end_term != end_term:
            row.end_term = end_term
            changed = True
        if changed:
            db.add(row)
        return False

    row = Politician(
        name=name.strip(),
        party=party.strip() if party else None,
        position=position.strip(),
        city_id=city_id,
        state_id=state_id,
        start_term=start_term,
        end_term=end_term,
    )
    db.add(row)
    cache[key] = row
    return True
