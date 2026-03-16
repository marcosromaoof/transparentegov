from __future__ import annotations

import httpx
import time
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult
from app.models import City, Country, State


class IBGECollector:
    source_key = "ibge"

    def run(self, db: Session) -> CollectorResult:
        fetched = 0
        saved = 0

        brazil = db.scalar(select(Country).where(Country.code == "BR"))
        if not brazil:
            brazil = Country(name="Brasil", code="BR")
            db.add(brazil)
            db.flush()

        state_by_code = {
            row.code.upper(): row
            for row in db.scalars(select(State).where(State.country_id == brazil.id)).all()
        }
        city_by_ibge = {
            str(row.ibge_code): row for row in db.scalars(select(City).where(City.ibge_code.is_not(None))).all()
        }

        timeout = httpx.Timeout(timeout=45.0)
        with httpx.Client(timeout=timeout) as client:
            states_response = self._get_with_retry(
                client, "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
            )
            if states_response is None:
                return CollectorResult(fetched=0, saved=0)
            states_payload = states_response.json()
            fetched += len(states_payload)

            for item in states_payload:
                state_code = str(item.get("sigla") or "").upper()
                state_name = str(item.get("nome") or "").strip()
                if not state_code or not state_name:
                    continue

                row = state_by_code.get(state_code)
                if row:
                    if row.name != state_name:
                        row.name = state_name
                        db.add(row)
                    continue

                row = State(country_id=brazil.id, name=state_name, code=state_code)
                db.add(row)
                db.flush()
                state_by_code[state_code] = row
                saved += 1

            for state_code, state in state_by_code.items():
                response = self._get_with_retry(
                    client,
                    f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{state_code}/municipios"
                )
                if response is None:
                    continue
                cities = response.json()
                fetched += len(cities)
                for item in cities:
                    ibge_code = str(item.get("id") or "").strip()
                    city_name = str(item.get("nome") or "").strip()
                    if not ibge_code or not city_name:
                        continue

                    row = city_by_ibge.get(ibge_code)
                    if row:
                        changed = False
                        if row.state_id != state.id:
                            row.state_id = state.id
                            changed = True
                        if row.name != city_name:
                            row.name = city_name
                            changed = True
                        if changed:
                            db.add(row)
                        continue

                    db.add(City(state_id=state.id, name=city_name, ibge_code=ibge_code))
                    saved += 1
                    if saved % 500 == 0:
                        db.flush()

        db.commit()
        return CollectorResult(fetched=fetched, saved=saved)

    def _get_with_retry(
        self,
        client: httpx.Client,
        url: str,
        *,
        attempts: int = 3,
    ) -> httpx.Response | None:
        for attempt in range(1, attempts + 1):
            try:
                response = client.get(url)
                response.raise_for_status()
                return response
            except httpx.HTTPError:
                if attempt == attempts:
                    return None
                time.sleep(attempt * 1.5)
        return None

