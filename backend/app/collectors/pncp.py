from __future__ import annotations

from datetime import date, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult
from app.collectors.common import normalize_text, parse_date, parse_decimal_value
from app.core.config import get_settings
from app.models import City, Contract, DatasetSource, PublicAgency, PublicSpending


class PNCPCollector:
    source_key = "pncp"

    def run(self, db: Session) -> CollectorResult:
        settings = get_settings()

        source = db.scalar(select(DatasetSource).where(DatasetSource.source_key == self.source_key))
        today = date.today()
        default_start = today - timedelta(days=max(settings.pncp_days_back, 1))
        start_date = default_start
        if source and source.last_run_at:
            candidate = source.last_run_at.date() - timedelta(days=1)
            start_date = max(default_start, candidate)

        page_size = min(max(settings.pncp_page_size, 10), 200)
        max_pages = max(settings.pncp_max_pages, 1)

        city_by_ibge = self._load_city_by_ibge(db)
        agency_cache = self._load_agency_cache(db)
        contract_keys_by_agency: dict[int, set[tuple[str, str, date | None, date | None, str]]] = {}
        spending_keys_by_agency: dict[int, set[tuple[int, int, str, str]]] = {}

        fetched = 0
        saved = 0
        inserted_counter = 0

        timeout = httpx.Timeout(timeout=45.0)
        with httpx.Client(timeout=timeout) as client:
            for page in range(1, max_pages + 1):
                params = {
                    "dataInicial": start_date.strftime("%Y%m%d"),
                    "dataFinal": today.strftime("%Y%m%d"),
                    "pagina": page,
                    "tamanhoPagina": page_size,
                }
                response = client.get(f"{settings.pncp_base_url}/contratos", params=params)
                response.raise_for_status()
                payload = response.json()
                rows = payload.get("data") or []
                if not rows:
                    break

                fetched += len(rows)
                for row in rows:
                    created, inserted = self._ingest_row(
                        db,
                        row=row,
                        city_by_ibge=city_by_ibge,
                        agency_cache=agency_cache,
                        contract_keys_by_agency=contract_keys_by_agency,
                        spending_keys_by_agency=spending_keys_by_agency,
                    )
                    saved += created
                    inserted_counter += inserted
                    if inserted_counter >= 500:
                        db.flush()
                        inserted_counter = 0

                total_pages = int(payload.get("totalPaginas") or 0)
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
        if not agency:
            agency = PublicAgency(
                city_id=city.id,
                name=agency_name[:255],
                type=self._resolve_agency_type(row),
                address=self._build_address(unidade),
            )
            db.add(agency)
            db.flush()
            agency_cache[agency_key] = agency
            inserted_rows += 1

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
