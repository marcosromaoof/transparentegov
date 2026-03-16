from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Investigation, InvestigationEntity, InvestigationNote


def list_investigations(db: Session) -> list[Investigation]:
    return db.scalars(select(Investigation).order_by(Investigation.updated_at.desc())).all()


def create_investigation(
    db: Session,
    *,
    title: str,
    summary: str | None,
    scope_country_id: int | None,
    scope_state_id: int | None,
    scope_city_id: int | None,
) -> Investigation:
    item = Investigation(
        title=title,
        summary=summary,
        scope_country_id=scope_country_id,
        scope_state_id=scope_state_id,
        scope_city_id=scope_city_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_investigation(db: Session, investigation_id: int) -> Investigation:
    item = db.get(Investigation, investigation_id)
    if not item:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return item


def add_entity(
    db: Session,
    investigation_id: int,
    *,
    entity_type: str,
    entity_id: int,
    note: str | None,
) -> InvestigationEntity:
    get_investigation(db, investigation_id)
    row = InvestigationEntity(
        investigation_id=investigation_id,
        entity_type=entity_type,
        entity_id=entity_id,
        note=note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_entities(db: Session, investigation_id: int) -> list[InvestigationEntity]:
    get_investigation(db, investigation_id)
    return db.scalars(
        select(InvestigationEntity).where(InvestigationEntity.investigation_id == investigation_id)
    ).all()


def add_note(db: Session, investigation_id: int, body: str) -> InvestigationNote:
    get_investigation(db, investigation_id)
    row = InvestigationNote(investigation_id=investigation_id, body=body)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_notes(db: Session, investigation_id: int) -> list[InvestigationNote]:
    get_investigation(db, investigation_id)
    return db.scalars(
        select(InvestigationNote)
        .where(InvestigationNote.investigation_id == investigation_id)
        .order_by(InvestigationNote.created_at.desc())
    ).all()

