from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult
from app.models import City, State


class IBGECollector:
    source_key = "ibge"

    def run(self, db: Session) -> CollectorResult:
        states = db.scalars(select(State)).all()
        fetched = 0
        saved = 0
        with httpx.Client(timeout=30.0) as client:
            for state in states:
                response = client.get(
                    f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{state.code}/municipios"
                )
                if response.status_code >= 400:
                    continue
                cities = response.json()
                fetched += len(cities)
                for item in cities:
                    ibge_code = str(item.get("id"))
                    exists = db.scalar(
                        select(City).where(City.state_id == state.id, City.ibge_code == ibge_code)
                    )
                    if exists:
                        continue
                    db.add(
                        City(
                            state_id=state.id,
                            name=item.get("nome", "Municipio sem nome"),
                            ibge_code=ibge_code,
                        )
                    )
                    saved += 1
        db.commit()
        return CollectorResult(fetched=fetched, saved=saved)

