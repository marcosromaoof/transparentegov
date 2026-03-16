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