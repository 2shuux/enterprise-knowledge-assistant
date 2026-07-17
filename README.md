# Enterprise Knowledge Assistant

AI-powered knowledge base: upload your organization's documents, ask questions,
get grounded answers with page-level citations. Built with RAG, hybrid search,
and streaming responses.

**Stack:** React 19 · TypeScript · MUI · React Query | FastAPI · SQLAlchemy ·
PostgreSQL · ChromaDB · Redis | Gemini (swappable LLM provider) | Docker · GitHub Actions

## Quickstart (development)

Prereqs: Docker (or Colima), Python 3.12+, Node 20+.

```bash
# 1. infrastructure (Postgres, Redis, ChromaDB)
docker compose up -d

# 2. backend  (terminal 2)
cd apps/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../../.env.example .env        # then edit .env with your keys
uvicorn app.main:app --reload --app-dir src

# 3. frontend (terminal 3)
cd apps/frontend
npm install
npm run dev
```

Open http://localhost:5173 — the landing page's status chip proves the
frontend → API loop. Swagger UI: http://localhost:8000/api/docs

## Verify

```bash
cd apps/backend && ruff check src tests && pytest   # lint + tests
cd apps/frontend && npm run typecheck               # types
```

## Fully containerized stack (optional)

```bash
docker compose --profile full up --build
# app served by nginx at http://localhost:8080
```

## Repository layout

```
apps/backend    FastAPI service (src layout, tests, ruff)
apps/frontend   React 19 + Vite + MUI
docker/         Dockerfiles + nginx config
docs/           architecture & ADRs
.github/        CI pipeline
```
