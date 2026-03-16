from __future__ import annotations

from datetime import date
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult
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

        deputados_url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
        params = {"itens": 25, "ordem": "ASC", "ordenarPor": "nome"}
        headers = {"accept": "application/json"}
        with httpx.Client(timeout=30.0) as client:
            deputados_response = client.get(deputados_url, params=params, headers=headers)
            deputados_response.raise_for_status()
            deputados = deputados_response.json().get("dados", [])

            data = []
            for deputado in deputados:
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

        saved = 0
        for item in data:
            value = Decimal(str(item.get("valorDocumento") or 0))
            if value <= 0:
                continue

            entry = PublicSpending(
                agency_id=agency.id,
                year=int(item.get("ano") or date.today().year),
                month=int(item.get("mes") or 1),
                category=item.get("tipoDespesa") or "Despesa parlamentar",
                value=value,
            )
            db.add(entry)
            saved += 1

            supplier = item.get("nomeFornecedor") or "Fornecedor nao informado"
            contract = Contract(
                agency_id=agency.id,
                supplier=supplier[:255],
                value=value,
                start_date=date.today(),
                end_date=None,
                description=(item.get("tipoDespesa") or "Despesa parlamentar")[:1000],
            )
            db.add(contract)
            saved += 1

        db.commit()
        return CollectorResult(fetched=len(data), saved=saved)

