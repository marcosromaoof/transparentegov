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

## Validação da produção via proxy frontend

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate_vercel_proxy.ps1 -BaseUrl "https://transparentegov.vercel.app" -AdminKey "<ADMIN_API_KEY>"
```
