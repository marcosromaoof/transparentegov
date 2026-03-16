from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
import re

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult
from app.collectors.common import normalize_text, parse_decimal_value
from app.core.config import get_settings
from app.models import City, ParliamentaryAmendment, Politician, State


class PortalTransparenciaCollector:
    source_key = "portal_transparencia"

    def run(self, db: Session) -> CollectorResult:
        settings = get_settings()
        api_key = (settings.portal_transparencia_api_key or "").strip()
        if not api_key:
            raise RuntimeError(
                "PORTAL_TRANSPARENCIA_API_KEY nao configurada. Cadastre uma chave em "
                "https://www.portaldatransparencia.gov.br/api-de-dados/cadastrar-email e "
                "defina a variavel de ambiente."
            )

        states_by_code = {row.code.upper(): row for row in db.scalars(select(State)).all()}
        city_by_state_name, unique_city_by_name = self._load_city_indexes(db)
        politicians_by_name = self._load_politicians_by_name(db)
        existing_keys = self._load_existing_amendment_keys(db)

        current_year = date.today().year
        start_year = max(2015, current_year - max(settings.portal_emendas_years_back, 1) + 1)
        years = list(range(start_year, current_year + 1))

        fetched = 0
        saved = 0
        inserted_counter = 0
        timeout = httpx.Timeout(timeout=45.0)
        headers = {"chave-api-dados": api_key}

        with httpx.Client(timeout=timeout) as client:
            for year in years:
                for page in range(1, max(settings.portal_emendas_max_pages_per_year, 1) + 1):
                    response = client.get(
                        f"{settings.portal_transparencia_base_url}/api-de-dados/emendas",
                        params={"ano": year, "pagina": page},
                        headers=headers,
                    )
                    if response.status_code == 401:
                        raise RuntimeError("Chave da API do Portal da Transparencia invalida ou sem permissao.")
                    response.raise_for_status()
                    rows = response.json()
                    if not rows:
                        break

                    fetched += len(rows)
                    for row in rows:
                        created, inserted = self._ingest_row(
                            db,
                            row=row,
                            states_by_code=states_by_code,
                            city_by_state_name=city_by_state_name,
                            unique_city_by_name=unique_city_by_name,
                            politicians_by_name=politicians_by_name,
                            existing_keys=existing_keys,
                        )
                        saved += created
                        inserted_counter += inserted
                        if inserted_counter >= 500:
                            db.flush()
                            inserted_counter = 0

        db.commit()
        return CollectorResult(fetched=fetched, saved=saved)

    def _ingest_row(
        self,
        db: Session,
        *,
        row: dict,
        states_by_code: dict[str, State],
        city_by_state_name: dict[tuple[int, str], City],
        unique_city_by_name: dict[str, City | None],
        politicians_by_name: dict[str, list[Politician]],
        existing_keys: set[tuple[int, int | None, int, str, str]],
    ) -> tuple[int, int]:
        localidade = str(row.get("localidadeDoGasto") or "").strip()
        city = self._resolve_city(
            localidade=localidade,
            states_by_code=states_by_code,
            city_by_state_name=city_by_state_name,
            unique_city_by_name=unique_city_by_name,
        )
        if not city:
            return 0, 0

        value = self._resolve_emenda_value(row)
        if value <= 0:
            return 0, 0

        year = int(row.get("ano") or date.today().year)
        code = str(row.get("codigoEmenda") or "").strip()
        number = str(row.get("numeroEmenda") or "").strip()
        emenda_type = str(row.get("tipoEmenda") or "").strip()
        description = (
            f"[PORTAL_EMENDA {code}] {emenda_type} {number}".strip() or f"[PORTAL_EMENDA] Emenda {year}"
        )[:1000]

        politician = self._resolve_politician(
            author_name=str(row.get("nomeAutor") or row.get("autor") or "").strip(),
            city=city,
            politicians_by_name=politicians_by_name,
        )

        key = (city.id, politician.id if politician else None, year, str(value), description)
        if key in existing_keys:
            return 0, 0

        db.add(
            ParliamentaryAmendment(
                politician_id=politician.id if politician else None,
                city_id=city.id,
                value=value,
                year=year,
                description=description,
            )
        )
        existing_keys.add(key)
        return 1, 1

    def _resolve_city(
        self,
        *,
        localidade: str,
        states_by_code: dict[str, State],
        city_by_state_name: dict[tuple[int, str], City],
        unique_city_by_name: dict[str, City | None],
    ) -> City | None:
        if not localidade:
            return None

        uf_match = re.search(r"(?:-|/)\s*([A-Za-z]{2})\s*$", localidade)
        if uf_match:
            uf = uf_match.group(1).upper()
            state = states_by_code.get(uf)
            city_part = re.sub(r"(?:-|/)\s*([A-Za-z]{2})\s*$", "", localidade).strip()
            name_key = self._normalize_city_name(city_part)
            if state and name_key:
                match = city_by_state_name.get((state.id, name_key))
                if match:
                    return match

        name_key = self._normalize_city_name(localidade)
        if not name_key:
            return None
        return unique_city_by_name.get(name_key)

    def _normalize_city_name(self, value: str | None) -> str:
        text = normalize_text(value)
        for prefix in ("municipio de ", "município de ", "cidade de ", "mun de "):
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()
        return text

    def _resolve_politician(
        self,
        *,
        author_name: str,
        city: City,
        politicians_by_name: dict[str, list[Politician]],
    ) -> Politician | None:
        if not author_name:
            return None
        candidates = politicians_by_name.get(normalize_text(author_name), [])
        if not candidates:
            return None
        for row in candidates:
            if row.state_id == city.state_id:
                return row
        return candidates[0]

    def _resolve_emenda_value(self, row: dict) -> Decimal:
        for field in ("valorPago", "valorLiquidado", "valorEmpenhado", "valorRestoPago"):
            value = parse_decimal_value(row.get(field))
            if value > 0:
                return value
        return Decimal("0")

    def _load_city_indexes(
        self,
        db: Session,
    ) -> tuple[dict[tuple[int, str], City], dict[str, City | None]]:
        rows = db.scalars(select(City)).all()
        by_state_name: dict[tuple[int, str], City] = {}
        by_name_list: dict[str, list[City]] = defaultdict(list)
        for row in rows:
            normalized = self._normalize_city_name(row.name)
            by_state_name[(row.state_id, normalized)] = row
            by_name_list[normalized].append(row)

        by_unique_name: dict[str, City | None] = {}
        for name, items in by_name_list.items():
            by_unique_name[name] = items[0] if len(items) == 1 else None
        return by_state_name, by_unique_name

    def _load_politicians_by_name(self, db: Session) -> dict[str, list[Politician]]:
        mapping: dict[str, list[Politician]] = defaultdict(list)
        for row in db.scalars(select(Politician)).all():
            mapping[normalize_text(row.name)].append(row)
        return mapping

    def _load_existing_amendment_keys(
        self,
        db: Session,
    ) -> set[tuple[int, int | None, int, str, str]]:
        rows = db.scalars(select(ParliamentaryAmendment)).all()
        return {
            (row.city_id, row.politician_id, row.year, str(row.value), row.description or "")
            for row in rows
        }

