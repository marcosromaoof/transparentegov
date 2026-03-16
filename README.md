# TransparenteGov OSINT Platform

Plataforma profissional de investigação de dados públicos orientada a investigação territorial.

## Arquitetura

- `backend/`: FastAPI + PostgreSQL + Redis + Celery
- `frontend/`: Next.js investigativo (Busca OSINT, Entidades, Relações, Investigações, Datasets, Relatórios, Admin)
- `infra/`: docker-compose para execução local

## Requisitos atendidos

- fluxo investigativo territorial como tela principal (sem dashboard genérico inicial)
- schema completo de dados públicos territoriais e financeiros
- coleta automatizada com normalização e persistência (piloto Câmara + IBGE)
- painel admin separado com configuração de provedores IA
- provedores IA: `deepseek`, `google`, `openai`, `openrouter`, `groq`
- sincronização real de modelos via API de cada provedor
- seleção persistente de 1 modelo ativo (sem fallback)
- geração de relatórios investigativos em Markdown/PDF

## Setup rápido local

### 1) Infra

```bash
cd infra
docker compose up -d
```

### 2) Backend

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

### 3) Frontend

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Acesse [http://localhost:3000](http://localhost:3000).

## Configuração de IA (Admin)

1. Abrir `/admin`
2. Salvar chave API no provedor desejado
3. Clicar em `Buscar modelos`
4. Selecionar provedor/modelo em `Modelo Ativo do Sistema`

Sem modelo ativo configurado, a análise IA retorna erro (comportamento esperado, sem fallback).