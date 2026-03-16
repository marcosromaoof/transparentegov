from __future__ import annotations

from datetime import date, timedelta
import time

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult
from app.collectors.common import normalize_text, parse_date, parse_decimal_value
from app.core.config import get_settings
from app.models import (
    City,
    Contract,
    DatasetSource,
    Hospital,
    PoliceUnit,
    PublicAgency,
    PublicSpending,
    School,
)


class PNCPCollector:
    source_key = "pncp"

    def run(self, db: Session) -> CollectorResult:
        settings = get_settings()

        source = db.scalar(select(DatasetSource).where(DatasetSource.source_key == self.source_key))
        today = date.today()
        incremental_start = today - timedelta(days=max(settings.pncp_days_back, 1))
        backfill_start = today - timedelta(days=max(settings.pncp_backfill_days, 30))

        page_size = min(max(settings.pncp_page_size, 10), 200)
        agency_city_coverage = db.scalar(select(func.count(func.distinct(PublicAgency.city_id)))) or 0
        min_city_coverage = max(settings.pncp_backfill_min_cities, 1)
        use_incremental_window = bool(
            source and source.last_run_at and agency_city_coverage >= min_city_coverage
        )

        if use_incremental_window and source and source.last_run_at:
            start_date = max(incremental_start, source.last_run_at.date() - timedelta(days=1))
            max_pages = max(settings.pncp_max_pages, 1)
        else:
            start_date = backfill_start
            max_pages = max(settings.pncp_backfill_max_pages, 1)

        city_by_ibge = self._load_city_by_ibge(db)
        agency_cache = self._load_agency_cache(db)
        infrastructure_cache = self._load_infrastructure_cache(db)
        contract_keys_by_agency: dict[int, set[tuple[str, str, date | None, date | None, str]]] = {}
        spending_keys_by_agency: dict[int, set[tuple[int, int, str, str]]] = {}

        fetched = 0
        saved = 0
        inserted_counter = 0
        started_at = time.monotonic()
        runtime_budget = max(settings.pncp_max_runtime_seconds, 30)

        timeout = httpx.Timeout(timeout=45.0)
        with httpx.Client(timeout=timeout) as client:
            for page in range(1, max_pages + 1):
                if time.monotonic() - started_at >= runtime_budget:
                    break
                params = {
                    "dataInicial": start_date.strftime("%Y%m%d"),
                    "dataFinal": today.strftime("%Y%m%d"),
                    "pagina": page,
                    "tamanhoPagina": page_size,
                }
                response = client.get(f"{settings.pncp_base_url}/contratos", params=params)
                response.raise_for_status()
                payload = response.json()
                rows = self._extract_rows(payload)
                if not rows:
                    break

                fetched += len(rows)
                for row in rows:
                    created, inserted = self._ingest_row(
                        db,
                        row=row,
                        city_by_ibge=city_by_ibge,
                        agency_cache=agency_cache,
                        infrastructure_cache=infrastructure_cache,
                        contract_keys_by_agency=contract_keys_by_agency,
                        spending_keys_by_agency=spending_keys_by_agency,
                    )
                    saved += created
                    inserted_counter += inserted
                    if inserted_counter >= 500:
                        db.flush()
                        inserted_counter = 0

                total_pages = self._extract_total_pages(payload)
                if total_pages and page >= total_pages:
                    break

        db.commit()
        return CollectorResult(fetched=fetched, saved=saved)

    def _ingest_row(
        self,
        db: Session,
        *,
        row: dict,
        city_by_ibge: dict[str, City],
        agency_cache: dict[tuple[int, str], PublicAgency],
        infrastructure_cache: set[tuple[str, int, str]],
        contract_keys_by_agency: dict[int, set[tuple[str, str, date | None, date | None, str]]],
        spending_keys_by_agency: dict[int, set[tuple[int, int, str, str]]],
    ) -> tuple[int, int]:
        unidade = row.get("unidadeOrgao") or {}
        ibge_code = str(unidade.get("codigoIbge") or "").strip()
        city = city_by_ibge.get(ibge_code) or city_by_ibge.get(ibge_code.zfill(7))
        if not city:
            return 0, 0

        agency_name = str(unidade.get("nomeUnidade") or "").strip()
        if not agency_name:
            agency_name = str((row.get("orgaoEntidade") or {}).get("razaoSocial") or "").strip()
        if not agency_name:
            agency_name = "Orgao publico PNCP"

        agency_key = (city.id, normalize_text(agency_name))
        agency = agency_cache.get(agency_key)
        inserted_rows = 0
        agency_type = self._resolve_agency_type(row)
        if not agency:
            agency = PublicAgency(
                city_id=city.id,
                name=agency_name[:255],
                type=agency_type,
                address=self._build_address(unidade),
            )
            db.add(agency)
            db.flush()
            agency_cache[agency_key] = agency
            inserted_rows += 1
        else:
            agency_type = agency.type

        inserted_rows += self._ensure_infrastructure_records(
            db,
            city=city,
            agency=agency,
            agency_type=agency_type,
            infrastructure_cache=infrastructure_cache,
        )

        control_code = str(
            row.get("numeroControlePNCP") or row.get("numeroControlePncpCompra") or row.get("numeroContratoEmpenho") or ""
        ).strip()
        value = parse_decimal_value(row.get("valorGlobal") or row.get("valorInicial") or row.get("valorParcela"))
        if value <= 0:
            return 0, inserted_rows

        start_date = parse_date(row.get("dataVigenciaInicio")) or parse_date(row.get("dataAssinatura"))
        end_date = parse_date(row.get("dataVigenciaFim"))
        supplier = str(row.get("nomeRazaoSocialFornecedor") or "Fornecedor nao informado").strip()[:255]
        object_description = str(row.get("objetoContrato") or "").strip()
        description = f"[PNCP {control_code}] {object_description}".strip()[:1000]

        contract_keys = contract_keys_by_agency.get(agency.id)
        if contract_keys is None:
            contract_keys = {
                (
                    existing.supplier,
                    str(existing.value),
                    existing.start_date,
                    existing.end_date,
                    existing.description or "",
                )
                for existing in db.scalars(select(Contract).where(Contract.agency_id == agency.id)).all()
            }
            contract_keys_by_agency[agency.id] = contract_keys

        contract_key = (supplier, str(value), start_date, end_date, description)
        created = 0
        if contract_key not in contract_keys:
            db.add(
                Contract(
                    agency_id=agency.id,
                    supplier=supplier,
                    value=value,
                    start_date=start_date,
                    end_date=end_date,
                    description=description or None,
                )
            )
            contract_keys.add(contract_key)
            created += 1
            inserted_rows += 1

        reference_date = (
            parse_date(row.get("dataPublicacaoPncp"))
            or parse_date(row.get("dataAssinatura"))
            or parse_date(row.get("dataAtualizacaoGlobal"))
            or date.today()
        )
        category_name = str((row.get("categoriaProcesso") or {}).get("nome") or "Contrato publico")
        category = f"PNCP - {category_name}"[:128]

        spending_keys = spending_keys_by_agency.get(agency.id)
        if spending_keys is None:
            spending_keys = {
                (
                    existing.year,
                    existing.month,
                    existing.category,
                    str(existing.value),
                )
                for existing in db.scalars(select(PublicSpending).where(PublicSpending.agency_id == agency.id)).all()
            }
            spending_keys_by_agency[agency.id] = spending_keys

        spending_key = (reference_date.year, reference_date.month, category, str(value))
        if spending_key not in spending_keys:
            db.add(
                PublicSpending(
                    agency_id=agency.id,
                    year=spending_key[0],
                    month=spending_key[1],
                    category=spending_key[2],
                    value=value,
                )
            )
            spending_keys.add(spending_key)
            created += 1
            inserted_rows += 1

        return created, inserted_rows

    def _load_city_by_ibge(self, db: Session) -> dict[str, City]:
        rows = db.scalars(select(City).where(City.ibge_code.is_not(None))).all()
        return {str(row.ibge_code): row for row in rows if row.ibge_code}

    def _load_agency_cache(self, db: Session) -> dict[tuple[int, str], PublicAgency]:
        rows = db.scalars(select(PublicAgency)).all()
        return {(row.city_id, normalize_text(row.name)): row for row in rows}

    def _load_infrastructure_cache(self, db: Session) -> set[tuple[str, int, str]]:
        cache: set[tuple[str, int, str]] = set()
        for row in db.scalars(select(Hospital)).all():
            cache.add(("hospital", row.city_id, normalize_text(row.name)))
        for row in db.scalars(select(School)).all():
            cache.add(("school", row.city_id, normalize_text(row.name)))
        for row in db.scalars(select(PoliceUnit)).all():
            cache.add(("police_station", row.city_id, normalize_text(row.name)))
        return cache

    def _ensure_infrastructure_records(
        self,
        db: Session,
        *,
        city: City,
        agency: PublicAgency,
        agency_type: str,
        infrastructure_cache: set[tuple[str, int, str]],
    ) -> int:
        normalized_name = normalize_text(agency.name)
        if not normalized_name:
            return 0

        if agency_type == "hospital":
            cache_key = ("hospital", city.id, normalized_name)
            if cache_key in infrastructure_cache:
                return 0
            db.add(Hospital(city_id=city.id, name=agency.name[:255], address=agency.address, public=True))
            infrastructure_cache.add(cache_key)
            return 1

        if agency_type == "school":
            cache_key = ("school", city.id, normalized_name)
            if cache_key in infrastructure_cache:
                return 0
            db.add(School(city_id=city.id, name=agency.name[:255], type="publica", address=agency.address))
            infrastructure_cache.add(cache_key)
            return 1

        if agency_type == "police_station":
            cache_key = ("police_station", city.id, normalized_name)
            if cache_key in infrastructure_cache:
                return 0
            db.add(
                PoliceUnit(
                    city_id=city.id,
                    name=agency.name[:255],
                    address=agency.address,
                    type="police_station",
                )
            )
            infrastructure_cache.add(cache_key)
            return 1

        return 0

    def _extract_rows(self, payload: object) -> list[dict]:
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if not isinstance(payload, dict):
            return []
        rows = (
            payload.get("data")
            or payload.get("dados")
            or payload.get("items")
            or payload.get("resultados")
            or []
        )
        if not isinstance(rows, list):
            return []
        return [row for row in rows if isinstance(row, dict)]

    def _extract_total_pages(self, payload: object) -> int:
        if not isinstance(payload, dict):
            return 0
        raw_value = payload.get("totalPaginas") or payload.get("total_paginas") or payload.get("totalPages")
        try:
            return int(raw_value or 0)
        except (TypeError, ValueError):
            return 0

    def _resolve_agency_type(self, row: dict) -> str:
        category = normalize_text((row.get("categoriaProcesso") or {}).get("nome"))
        unit_name = normalize_text((row.get("unidadeOrgao") or {}).get("nomeUnidade"))
        haystack = f"{category} {unit_name}"
        if "hospital" in haystack:
            return "hospital"
        if "escola" in haystack or "educ" in haystack:
            return "school"
        if "polic" in haystack or "delegacia" in haystack:
            return "police_station"
        if "saude" in haystack:
            return "health_unit"
        if "bombeiro" in haystack:
            return "fire_department"
        if "secretaria" in haystack:
            return "secretariat"
        return "public_department"

    def _build_address(self, unidade: dict) -> str | None:
        city = str(unidade.get("municipioNome") or "").strip()
        uf = str(unidade.get("ufSigla") or "").strip()
        if city and uf:
            return f"{city}/{uf}"
        return city or uf or None
