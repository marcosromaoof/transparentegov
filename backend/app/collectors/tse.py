from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
import tempfile
import time
import zipfile

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.collectors.base import CollectorResult
from app.collectors.common import (
    load_city_indexes,
    load_politician_cache,
    load_states_by_code,
    normalize_text,
    upsert_politician,
)
from app.collectors.ibge import IBGECollector
from app.models import City, Politician, State


POSITION_MAP = {
    "vereador": "Vereador",
    "prefeito": "Prefeito",
    "governador": "Governador",
    "senador": "Senador",
    "deputado federal": "Deputado Federal",
    "deputado estadual": "Deputado Estadual",
    "deputado distrital": "Deputado Distrital",
}

YEARS = (2024, 2022)


class TSECollector:
    source_key = "tse"

    def run(self, db: Session) -> CollectorResult:
        self._ensure_territory_loaded(db)

        states_by_code = load_states_by_code(db)
        city_by_state_name, city_by_ibge = load_city_indexes(db)
        cache = load_politician_cache(db)

        fetched = 0
        saved = 0
        for year in YEARS:
            year_fetched, year_saved = self._collect_year(
                db,
                year=year,
                states_by_code=states_by_code,
                city_by_state_name=city_by_state_name,
                city_by_ibge=city_by_ibge,
                cache=cache,
            )
            fetched += year_fetched
            saved += year_saved

        db.commit()
        return CollectorResult(fetched=fetched, saved=saved)

    def _ensure_territory_loaded(self, db: Session) -> None:
        state_count = db.scalar(select(func.count(State.id))) or 0
        city_count = db.scalar(select(func.count(City.id))) or 0
        if state_count >= 27 and city_count >= 5500:
            return
        IBGECollector().run(db)

    def _collect_year(
        self,
        db: Session,
        *,
        year: int,
        states_by_code: dict[str, State],
        city_by_state_name: dict[tuple[int, str], City],
        city_by_ibge: dict[str, City],
        cache: dict[tuple[str, str, int | None, int | None], Politician],
    ) -> tuple[int, int]:
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_{year}.zip"
        try:
            archive_path = self._download_archive(url)
        except (httpx.HTTPError, RuntimeError):
            return 0, 0

        fetched = 0
        saved = 0
        seen_candidates: set[tuple[str, str, str, str]] = set()
        flush_counter = 0

        try:
            with zipfile.ZipFile(archive_path) as zf:
                csv_name = self._resolve_csv_name(zf, year)
                with zf.open(csv_name) as source:
                    reader = csv.DictReader(
                        (line.decode("latin-1", errors="ignore") for line in source),
                        delimiter=";",
                    )
                    for row in reader:
                        position = POSITION_MAP.get(normalize_text(row.get("DS_CARGO")))
                        if not position:
                            continue

                        election_status = normalize_text(
                            row.get("DS_SIT_TOT_TURNO") or row.get("DS_SITUACAO_CANDIDATURA")
                        )
                        if "eleit" not in election_status:
                            continue

                        candidate_id = str(row.get("SQ_CANDIDATO") or "").strip()
                        uf_code = str(row.get("SG_UF") or "").upper().strip()
                        ue_code = str(row.get("SG_UE") or "").strip()
                        dedupe_key = (candidate_id, position, uf_code, ue_code)
                        if candidate_id and dedupe_key in seen_candidates:
                            continue
                        seen_candidates.add(dedupe_key)

                        state = states_by_code.get(uf_code)
                        state_id = state.id if state else None
                        city_id = None
                        if position in {"Prefeito", "Vereador"} and state_id:
                            city = self._resolve_city(
                                row=row,
                                state_id=state_id,
                                city_by_state_name=city_by_state_name,
                                city_by_ibge=city_by_ibge,
                            )
                            city_id = city.id if city else None

                        start_term, end_term = self._resolve_term(position=position, year=year)
                        name = str(row.get("NM_URNA_CANDIDATO") or row.get("NM_CANDIDATO") or "").strip()
                        if not name:
                            continue

                        if upsert_politician(
                            db,
                            cache,
                            name=name,
                            party=row.get("SG_PARTIDO"),
                            position=position,
                            state_id=state_id,
                            city_id=city_id,
                            start_term=start_term,
                            end_term=end_term,
                        ):
                            saved += 1
                            flush_counter += 1
                            if flush_counter % 1000 == 0:
                                db.flush()
                        fetched += 1
        finally:
            archive_path.unlink(missing_ok=True)

        return fetched, saved

    def _resolve_city(
        self,
        *,
        row: dict[str, str],
        state_id: int,
        city_by_state_name: dict[tuple[int, str], City],
        city_by_ibge: dict[str, City],
    ) -> City | None:
        ue_code = str(row.get("SG_UE") or "").strip()
        if ue_code.isdigit():
            city = city_by_ibge.get(ue_code)
            if city:
                return city
            city = city_by_ibge.get(ue_code.zfill(7))
            if city:
                return city

        city_name = str(row.get("NM_UE") or "").strip()
        if not city_name:
            return None
        return city_by_state_name.get((state_id, normalize_text(city_name)))

    def _download_archive(self, url: str) -> Path:
        timeout = httpx.Timeout(connect=30.0, read=None, write=30.0, pool=60.0)
        attempts = 4
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                temp_path = Path(tmp.name)
                try:
                    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                        with client.stream("GET", url) as response:
                            response.raise_for_status()
                            for chunk in response.iter_bytes(chunk_size=1024 * 256):
                                if chunk:
                                    tmp.write(chunk)
                    return temp_path
                except (httpx.HTTPError, RuntimeError) as exc:
                    last_error = exc
                    temp_path.unlink(missing_ok=True)
                    if attempt < attempts:
                        time.sleep(attempt * 2)

        if last_error:
            raise last_error
        raise RuntimeError(f"Falha no download do arquivo TSE: {url}")

    def _resolve_csv_name(self, zf: zipfile.ZipFile, year: int) -> str:
        preferred = [name for name in zf.namelist() if name.endswith(f"consulta_cand_{year}_BRASIL.csv")]
        if preferred:
            return preferred[0]
        fallback = [name for name in zf.namelist() if f"consulta_cand_{year}" in name and name.endswith(".csv")]
        if fallback:
            return fallback[0]
        raise RuntimeError(f"CSV da eleicao {year} nao encontrado no arquivo zip")

    def _resolve_term(self, *, position: str, year: int) -> tuple[date | None, date | None]:
        if position in {"Prefeito", "Vereador"} and year == 2024:
            return date(2025, 1, 1), date(2028, 12, 31)

        if position in {"Governador", "Deputado Federal", "Deputado Estadual", "Deputado Distrital"} and year == 2022:
            return date(2023, 1, 1), date(2026, 12, 31)

        if position == "Senador" and year == 2022:
            return date(2023, 2, 1), date(2031, 1, 31)

        return None, None
