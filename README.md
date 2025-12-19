# WebScraper Platform

Full-stack web scraping platform with FastAPI, Celery workers, PostgreSQL, Redis, Playwright scraping, and a Next.js 14 dashboard.

## Features
- Topic campaigns with auto-crawl, deduped link following, and page storage
- CSV/JSON export for results
- Worker and beat processes for background jobs
- Health and monitoring endpoints

## Architecture
- Frontend: Next.js 14 (App Router)
- Backend: FastAPI + SQLAlchemy + Alembic, Celery workers/beat
- Data stores: PostgreSQL, Redis
- Dev orchestration: Docker Compose (Postgres, Redis, backend, worker, beat, frontend, Flower)

## Project Structure
```
backend/   # FastAPI app, Celery, Alembic migrations, helper scripts
frontend/  # Next.js dashboard
docker-compose.yml
Makefile
.env.example
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

## Deployment Notes (Render)
- DB-using services: `backend` (API), `worker`, `beat`. They must share the same `DATABASE_URL`.
- Render env vars (Dashboard → Service → Environment):
  - `DATABASE_URL` = Internal Database URL for **webscraper-db-prod**.
  - `REDIS_URL` (and optionally `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`) = your Redis URL.
  - Keep `SECRET_KEY`, `ENVIRONMENT`, `CORS_ORIGINS` set per environment.
- Automatic migrations: add a Pre-Deploy Command on the API service:  
  `cd backend && python -m scripts.migrate`  
  Deploy will fail (non-zero) if migrations fail.
- Manual migrations: `cd backend && python -m scripts.migrate`
- DB connectivity check: `cd backend && python -m scripts.db_ping`
- Start commands:
  - API: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Worker: `celery -A app.workers.celery_app worker --loglevel=info`
  - Beat: `celery -A app.workers.celery_app beat --loglevel=info`
- Health: `GET /api/v1/health` returns service info plus `db` reachability.

## Useful Make targets
- `make dev` — start all services with logs
- `make migrate` / `make migrate-create MESSAGE="desc"` — Alembic
- `make logs-backend` / `make logs-worker` — tail logs
- `make format` / `make lint` — code quality

## Contributing
- Run formatting and lint checks before PRs.
- Keep secrets out of git; use env vars for all credentials.
