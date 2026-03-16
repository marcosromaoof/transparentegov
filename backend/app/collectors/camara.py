from __future__ import annotations

from datetime import date
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult
from app.collectors.common import (
    load_politician_cache,
    load_states_by_code,
    parse_date,
    upsert_politician,
)
from app.models import City, Contract, PublicAgency, PublicSpending


class CamaraCollector:
    source_key = "camara"

    def run(self, db: Session) -> CollectorResult:
        city = db.scalar(select(City).where(City.name == "Brasilia"))
        if not city:
            return CollectorResult(fetched=0, saved=0)

        agency = db.scalar(
            select(PublicAgency).where(
                PublicAgency.city_id == city.id, PublicAgency.name == "Camara dos Deputados"
            )
        )
        if not agency:
            agency = PublicAgency(
                city_id=city.id,
                name="Camara dos Deputados",
                type="public_department",
                address="Praca dos Tres Poderes - Brasilia",
            )
            db.add(agency)
            db.commit()
            db.refresh(agency)

        headers = {"accept": "application/json"}
        timeout = httpx.Timeout(timeout=45.0)
        with httpx.Client(timeout=timeout) as client:
            deputados = self._fetch_all_deputados(client, headers=headers)

            states_by_code = load_states_by_code(db)
            politician_cache = load_politician_cache(db)
            politicians_saved = 0
            for deputado in deputados:
                name = str(deputado.get("nome") or "").strip()
                if not name:
                    continue
                uf = str(deputado.get("siglaUf") or "").upper()
                state = states_by_code.get(uf)
                if upsert_politician(
                    db,
                    politician_cache,
                    name=name,
                    party=deputado.get("siglaPartido"),
                    position="Deputado Federal",
                    state_id=state.id if state else None,
                    city_id=None,
                    start_term=parse_date("2023-02-01"),
                    end_term=parse_date("2027-01-31"),
                ):
                    politicians_saved += 1

            data = []
            # Limita despesas por execução para manter tempo previsível no coletor manual.
            for deputado in deputados[:40]:
                deputado_id = deputado.get("id")
                if not deputado_id:
                    continue
                despesas_response = client.get(
                    f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/despesas",
                    params={"ano": date.today().year, "itens": 20},
                    headers=headers,
                )
                if despesas_response.status_code >= 400:
                    continue
                data.extend(despesas_response.json().get("dados", []))

        existing_spending = {
            (
                row.year,
                row.month,
                row.category,
                str(row.value),
            ): row
            for row in db.scalars(select(PublicSpending).where(PublicSpending.agency_id == agency.id)).all()
        }
        existing_contracts = {
            (
                row.supplier,
                str(row.value),
                row.description or "",
            ): row
            for row in db.scalars(select(Contract).where(Contract.agency_id == agency.id)).all()
        }
        saved = 0
        for item in data:
            value = Decimal(str(item.get("valorDocumento") or 0))
            if value <= 0:
                continue

            spending_key = (
                int(item.get("ano") or date.today().year),
                int(item.get("mes") or 1),
                (item.get("tipoDespesa") or "Despesa parlamentar"),
                str(value),
            )
            if spending_key not in existing_spending:
                entry = PublicSpending(
                    agency_id=agency.id,
                    year=spending_key[0],
                    month=spending_key[1],
                    category=spending_key[2],
                    value=value,
                )
                db.add(entry)
                existing_spending[spending_key] = entry
                saved += 1

            supplier = item.get("nomeFornecedor") or "Fornecedor nao informado"
            description = (item.get("tipoDespesa") or "Despesa parlamentar")[:1000]
            contract_key = (
                supplier[:255],
                str(value),
                description,
            )
            if contract_key not in existing_contracts:
                contract = Contract(
                    agency_id=agency.id,
                    supplier=contract_key[0],
                    value=value,
                    start_date=date.today(),
                    end_date=None,
                    description=contract_key[2],
                )
                db.add(contract)
                existing_contracts[contract_key] = contract
                saved += 1

        db.commit()
        return CollectorResult(fetched=len(deputados) + len(data), saved=saved + politicians_saved)

    def _fetch_all_deputados(
        self,
        client: httpx.Client,
        *,
        headers: dict[str, str],
    ) -> list[dict]:
        rows: list[dict] = []
        page = 1
        while True:
            response = client.get(
                "https://dadosabertos.camara.leg.br/api/v2/deputados",
                params={"itens": 100, "pagina": page, "ordem": "ASC", "ordenarPor": "nome"},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json().get("dados", [])
            if not payload:
                break
            rows.extend(payload)
            if len(payload) < 100:
                break
            page += 1
        return rows

