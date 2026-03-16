# Backend FastAPI

## Executar

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

## Worker de coleta

```bash
celery -A app.tasks.worker.celery_app worker -l INFO
celery -A app.tasks.worker.celery_app beat -l INFO
```

## Bootstrap completo (migrations + seed + coletores)

Command line direta:

```bash
python -m app.ops.bootstrap
```

PowerShell wrapper (um comando):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_full.ps1
```

Para usar o banco da Vercel Postgres:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_full.ps1 -DatabaseUrl "<DATABASE_URL_DA_VERCEL>"
```

## Configuracao de fontes com credencial

Para coletar dados reais de emendas no Portal da Transparencia, configure:

```bash
PORTAL_TRANSPARENCIA_API_KEY=<sua_chave_api>
```

A chave e obtida em:
`https://www.portaldatransparencia.gov.br/api-de-dados/cadastrar-email`

Para cobertura ampla de contratos/gastos por cidade no PNCP (primeiro ciclo), ajuste opcional:

```bash
PNCP_BACKFILL_DAYS=365
PNCP_BACKFILL_MAX_PAGES=120
PNCP_BACKFILL_MIN_CITIES=200
```

Com cobertura abaixo de `PNCP_BACKFILL_MIN_CITIES`, o coletor roda em modo backfill; depois disso, entra em modo incremental.

## Validação da produção via proxy frontend

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate_vercel_proxy.ps1 -BaseUrl "https://transparentegov.vercel.app" -AdminKey "<ADMIN_API_KEY>"
```
