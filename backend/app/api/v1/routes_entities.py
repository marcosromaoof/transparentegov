from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import DBSession
from app.models import Contract, Politician, PublicAgency

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/search")
def search_entities(
    db: DBSession,
    query: str = Query(min_length=2),
    city_id: int | None = Query(default=None),
) -> dict:
    agencies_stmt = select(PublicAgency).where(PublicAgency.name.ilike(f"%{query}%"))
    if city_id:
        agencies_stmt = agencies_stmt.where(PublicAgency.city_id == city_id)
    agencies = db.scalars(agencies_stmt.limit(30)).all()

    politicians_stmt = select(Politician).where(Politician.name.ilike(f"%{query}%"))
    if city_id:
        politicians_stmt = politicians_stmt.where(Politician.city_id == city_id)
    politicians = db.scalars(politicians_stmt.limit(30)).all()

    contracts = db.scalars(
        select(Contract).where(Contract.supplier.ilike(f"%{query}%")).limit(30)
    ).all()

    return {
        "agencies": [
            {"id": a.id, "name": a.name, "type": "public_agency", "city_id": a.city_id} for a in agencies
        ],
        "politicians": [
            {"id": p.id, "name": p.name, "type": "politician", "city_id": p.city_id}
            for p in politicians
        ],
        "contracts": [
            {
                "id": c.id,
                "name": c.supplier,
                "type": "contract",
                "agency_id": c.agency_id,
                "value": str(c.value),
            }
            for c in contracts
        ],
    }


@router.get("/{entity_type}/{entity_id}/relations")
def entity_relations(entity_type: str, entity_id: int, db: DBSession) -> dict:
    if entity_type == "public_agency":
        agency = db.get(PublicAgency, entity_id)
        if not agency:
            raise HTTPException(status_code=404, detail="Agency not found")
        contracts = db.scalars(select(Contract).where(Contract.agency_id == agency.id).limit(100)).all()
        nodes = [
            {"id": f"agency-{agency.id}", "label": agency.name, "type": "public_agency"},
        ]
        edges = []
        for contract in contracts:
            contract_node_id = f"contract-{contract.id}"
            supplier_node_id = f"supplier-{contract.id}"
            nodes.append(
                {
                    "id": contract_node_id,
                    "label": f"Contrato {contract.id}",
                    "type": "contract",
                    "value": str(contract.value),
                }
            )
            nodes.append(
                {
                    "id": supplier_node_id,
                    "label": contract.supplier,
                    "type": "supplier",
                }
            )
            edges.append(
                {
                    "source": f"agency-{agency.id}",
                    "target": contract_node_id,
                    "label": "contrata",
                }
            )
            edges.append({"source": contract_node_id, "target": supplier_node_id, "label": "fornecedor"})
        return {"nodes": nodes, "edges": edges}

    if entity_type == "politician":
        politician = db.get(Politician, entity_id)
        if not politician:
            raise HTTPException(status_code=404, detail="Politician not found")
        return {
            "nodes": [{"id": f"politician-{politician.id}", "label": politician.name, "type": "politician"}],
            "edges": [],
        }

    raise HTTPException(status_code=404, detail="Unsupported entity type")

