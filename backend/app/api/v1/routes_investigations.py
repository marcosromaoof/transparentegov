from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DBSession
from app.schemas.api import (
    InvestigationCreate,
    InvestigationEntityCreate,
    InvestigationEntityOut,
    InvestigationNoteCreate,
    InvestigationNoteOut,
    InvestigationOut,
)
from app.services.investigations import (
    add_entity,
    add_note,
    create_investigation,
    get_investigation,
    list_entities,
    list_investigations,
    list_notes,
)

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.get("", response_model=list[InvestigationOut])
def get_all(db: DBSession) -> list[InvestigationOut]:
    return [InvestigationOut.model_validate(item) for item in list_investigations(db)]


@router.post("", response_model=InvestigationOut)
def create(payload: InvestigationCreate, db: DBSession) -> InvestigationOut:
    item = create_investigation(
        db,
        title=payload.title,
        summary=payload.summary,
        scope_country_id=payload.scope_country_id,
        scope_state_id=payload.scope_state_id,
        scope_city_id=payload.scope_city_id,
    )
    return InvestigationOut.model_validate(item)


@router.get("/{investigation_id}", response_model=InvestigationOut)
def get_one(investigation_id: int, db: DBSession) -> InvestigationOut:
    return InvestigationOut.model_validate(get_investigation(db, investigation_id))


@router.get("/{investigation_id}/entities", response_model=list[InvestigationEntityOut])
def get_entities(investigation_id: int, db: DBSession) -> list[InvestigationEntityOut]:
    return [InvestigationEntityOut.model_validate(item) for item in list_entities(db, investigation_id)]


@router.post("/{investigation_id}/entities", response_model=InvestigationEntityOut)
def post_entity(
    investigation_id: int,
    payload: InvestigationEntityCreate,
    db: DBSession,
) -> InvestigationEntityOut:
    row = add_entity(
        db,
        investigation_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        note=payload.note,
    )
    return InvestigationEntityOut.model_validate(row)


@router.get("/{investigation_id}/notes", response_model=list[InvestigationNoteOut])
def get_notes(investigation_id: int, db: DBSession) -> list[InvestigationNoteOut]:
    return [InvestigationNoteOut.model_validate(item) for item in list_notes(db, investigation_id)]


@router.post("/{investigation_id}/notes", response_model=InvestigationNoteOut)
def post_note(
    investigation_id: int,
    payload: InvestigationNoteCreate,
    db: DBSession,
) -> InvestigationNoteOut:
    row = add_note(db, investigation_id, payload.body)
    return InvestigationNoteOut.model_validate(row)

