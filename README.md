# WebScraper Platform

FastAPI backend with Celery workers, PostgreSQL, Redis, Playwright-powered scraping, and a Next.js 14 dashboard.

## Features
- Topic campaigns with auto-crawl and deduped link following
- CSV/JSON exports for results
- Worker and beat processes for background jobs
- Health endpoints and DB connectivity checks

## Architecture
- Frontend: Next.js 14 (App Router)
- Backend: FastAPI + SQLAlchemy + Alembic; Celery worker/beat
- Data: PostgreSQL, Redis
- Dev orchestration: Docker Compose (Postgres, Redis, backend, worker, beat, frontend, Flower)

## Project Structure
```
backend/   # FastAPI app, Celery, Alembic migrations, helper scripts
frontend/  # Next.js dashboard
docker-compose.yml
Makefile
.env.example
render.yaml
```

## Getting Started (local)
Prereqs: Docker, Docker Compose, Make (optional).

1) Copy envs: `cp .env.example .env`
2) Start stack: `docker-compose up -d backend worker beat frontend`
3) Backend docs: http://localhost:8000/docs  
4) Frontend: http://localhost:3000  
5) Flower: http://localhost:5555

## Environment
See `.env.example` for all variables. Key ones:
- `DATABASE_URL` (PostgreSQL connection string)
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `SECRET_KEY`, `CORS_ORIGINS`, scraping timeouts, proxy settings

## Deployment to Render (API only)
- Blueprint-driven: `render.yaml` creates one Web Service (API) and one Postgres resource (`webscraper-db-prod`). `DATABASE_URL` is auto-injected from the database via `fromDatabase`, and `SECRET_KEY` is auto-generated.
- Deploy flow:
  1) Render → New → Blueprint Instance → select this repo.
  2) Confirm env vars: `DATABASE_URL` already wired to the database; `SECRET_KEY` generated; adjust `CORS_ORIGINS` if needed; keep `ENVIRONMENT=production`.
  3) Click Deploy. Pre-deploy runs `cd backend && alembic upgrade head`; deploy fails if migrations fail.
  4) Verify `https://<service-url>/health` (expects `{"status":"ok","db":true}`) and review logs.
- Start command (blueprint): `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Manual migrations fallback: `cd backend && alembic upgrade head`
- DB connectivity check: `cd backend && python -m scripts.db_ping`

## Useful Make targets
- `make dev` — start all services with logs
- `make migrate` / `make migrate-create MESSAGE="desc"` — Alembic
- `make logs-backend` / `make logs-worker` — tail logs
- `make format` / `make lint` — code quality

## Contributing
- Run formatting and lint checks before PRs.
- Keep secrets out of git; use env vars for all credentials.
