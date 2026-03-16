from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from app.collectors.registry import COLLECTORS
from app.db.seed import seed_data
from app.db.session import SessionLocal
from app.models import DatasetSource
from app.services.collectors import run_collector


DEFAULT_SOURCE_ORDER = [
    "ibge",
    "senado",
    "camara",
    "tse",
    "portal_transparencia",
    "pncp",
    "base_dos_dados",
]


@dataclass
class BootstrapResult:
    source_key: str
    status: str
    fetched: int
    saved: int
    error: str | None
    duration_s: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap completo do banco OSINT: migrations + seed + coletores.",
    )
    parser.add_argument(
        "--sources",
        default=",".join(DEFAULT_SOURCE_ORDER),
        help="Lista de coletores separados por virgula, na ordem de execucao.",
    )
    parser.add_argument("--skip-migrations", action="store_true", help="Nao executa alembic upgrade head.")
    parser.add_argument("--skip-seed", action="store_true", help="Nao executa seed_data().")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continua nos proximos coletores mesmo se um falhar.",
    )
    return parser.parse_args()


def run_migrations() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    alembic_ini = backend_root / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    command.upgrade(cfg, "head")


def ensure_sources_enabled(source_keys: list[str]) -> None:
    with SessionLocal() as db:
        rows = db.scalars(select(DatasetSource).where(DatasetSource.source_key.in_(source_keys))).all()
        for row in rows:
            if not row.enabled:
                row.enabled = True
                db.add(row)
        db.commit()


def run_bootstrap(
    *,
    source_keys: list[str],
    continue_on_error: bool,
) -> list[BootstrapResult]:
    results: list[BootstrapResult] = []
    for source_key in source_keys:
        started = perf_counter()
        try:
            with SessionLocal() as db:
                run = run_collector(db, source_key)
            results.append(
                BootstrapResult(
                    source_key=source_key,
                    status=run.status,
                    fetched=run.records_fetched,
                    saved=run.records_saved,
                    error=run.error_message,
                    duration_s=perf_counter() - started,
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                BootstrapResult(
                    source_key=source_key,
                    status="error",
                    fetched=0,
                    saved=0,
                    error=str(exc),
                    duration_s=perf_counter() - started,
                )
            )
            if not continue_on_error:
                break
    return results


def main() -> int:
    args = parse_args()
    source_keys = [item.strip() for item in args.sources.split(",") if item.strip()]
    invalid = [key for key in source_keys if key not in COLLECTORS]
    if invalid:
        print(f"[bootstrap] Coletores invalidos: {', '.join(invalid)}")
        print(f"[bootstrap] Coletores disponiveis: {', '.join(sorted(COLLECTORS))}")
        return 1

    print("[bootstrap] Iniciando pipeline...")
    print(f"[bootstrap] Ordem de coletores: {', '.join(source_keys)}")

    if not args.skip_migrations:
        print("[bootstrap] Executando migrations (alembic upgrade head)...")
        run_migrations()

    if not args.skip_seed:
        print("[bootstrap] Executando seed inicial...")
        seed_data()

    ensure_sources_enabled(source_keys)

    results = run_bootstrap(source_keys=source_keys, continue_on_error=args.continue_on_error)

    has_error = False
    print("[bootstrap] Resultado:")
    for row in results:
        duration = f"{row.duration_s:.1f}s"
        print(
            f"  - {row.source_key}: status={row.status} fetched={row.fetched} "
            f"saved={row.saved} duration={duration}"
        )
        if row.error:
            has_error = True
            print(f"    erro={row.error}")

    if has_error:
        print("[bootstrap] Concluido com falhas.")
        return 2

    print("[bootstrap] Concluido com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
