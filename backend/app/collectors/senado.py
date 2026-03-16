from __future__ import annotations

import httpx
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult
from app.collectors.common import (
    load_politician_cache,
    load_states_by_code,
    parse_date,
    upsert_politician,
)


class SenadoCollector:
    source_key = "senado"

    def run(self, db: Session) -> CollectorResult:
        timeout = httpx.Timeout(timeout=45.0)
        with httpx.Client(timeout=timeout) as client:
            response = client.get("https://legis.senado.leg.br/dadosabertos/senador/lista/atual.json")
            response.raise_for_status()
            payload = response.json()

        parlamentares = (
            payload.get("ListaParlamentarEmExercicio", {})
            .get("Parlamentares", {})
            .get("Parlamentar", [])
        )

        states_by_code = load_states_by_code(db)
        cache = load_politician_cache(db)
        saved = 0

        for row in parlamentares:
            identidade = row.get("IdentificacaoParlamentar") or {}
            mandato = row.get("Mandato") or {}

            name = str(identidade.get("NomeParlamentar") or "").strip()
            if not name:
                continue

            uf = str(identidade.get("UfParlamentar") or mandato.get("UfParlamentar") or "").upper()
            state = states_by_code.get(uf)

            primeira = mandato.get("PrimeiraLegislaturaDoMandato") or {}
            segunda = mandato.get("SegundaLegislaturaDoMandato") or {}
            start_term = parse_date(primeira.get("DataInicio"))
            end_term = parse_date(segunda.get("DataFim")) or parse_date(primeira.get("DataFim"))

            if upsert_politician(
                db,
                cache,
                name=name,
                party=identidade.get("SiglaPartidoParlamentar"),
                position="Senador",
                state_id=state.id if state else None,
                city_id=None,
                start_term=start_term,
                end_term=end_term,
            ):
                saved += 1

        db.commit()
        return CollectorResult(fetched=len(parlamentares), saved=saved)
