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

### Local dev (Windows + Docker Desktop)

Prereqs: Docker Desktop running; Node 18+; npm 9+.

1) Install JS deps (also installs `frontend/` deps automatically)
```
npm install
```
2) Start the full stack (db, redis, API in Docker; Next.js on the host):
```
npm run dev
```
   - Creates `.env` from `.env.example` if missing
   - Runs `docker compose up -d db redis api` and applies Alembic migrations
   - Waits for `http://localhost:8000/health` to report `db: true`
   - Starts Next.js dev server on http://localhost:3002

3) Open:
   - Frontend: http://localhost:3002
   - API: http://localhost:8000
   - API Docs (Swagger): http://localhost:8000/docs

Useful npm scripts:
- `npm run dev:logs` – follow API container logs
- `npm run dev:down` – stop containers
- `npm run dev:frontend` – run only the frontend on port 3002

Troubleshooting:
- If ports 5432/6379/8000/3002 are in use, stop the conflicting app or change the port in `.env`.
- Ensure Docker Desktop is running; `docker info` should succeed.
- If health never reaches `db: true`, run `docker compose logs api` for details.

## Useful Commands (Makefile)
- `make dev` – start all services with logs
- `make up` / `make down` – start/stop in background
- `make logs` / `make logs-backend` / `make logs-worker` – follow logs
- `make migrate` / `make migrate-create MESSAGE="desc"` – Alembic migrations
- `make seed` – seed sample data (requires your seed script)
- `make test` / `make test-backend` / `make test-frontend` – run tests
- `make format` / `make lint` – code quality helpers

## Environment
See `.env.example` for all variables. Key ones:
- `DATABASE_URL` (PostgreSQL connection string)
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `SECRET_KEY`, `CORS_ORIGINS`, scraping timeouts, proxy settings

## Deployment to Render (API only)
- Blueprint-driven: `render.yaml` creates one Web Service (API) and one Postgres resource (`webscraper-db-prod`). `DATABASE_URL` is auto-injected from the database via `fromDatabase`, and `SECRET_KEY` is auto-generated.
- Deploy flow:
  1) Render ? New ? Blueprint Instance ? select this repo.
  2) Confirm env vars: `DATABASE_URL` already wired to the database; `SECRET_KEY` generated; adjust `CORS_ORIGINS` if needed; keep `ENVIRONMENT=production`.
  3) Click Deploy. Pre-deploy runs `cd backend && alembic upgrade head`; deploy fails if migrations fail.
  4) Verify `https://<service-url>/health` (expects `{"status":"ok","db":true}`) and review logs.
- Start command (blueprint): `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Manual migrations fallback: `cd backend && alembic upgrade head`
- DB connectivity check: `cd backend && python -m scripts.db_ping`

## Useful Make targets
- `make dev` – start all services with logs
- `make migrate` / `make migrate-create MESSAGE="desc"` – Alembic
- `make logs-backend` / `make logs-worker` – tail logs
- `make format` / `make lint` – code quality

## Contributing
- Run formatting and lint checks before PRs.
- Keep secrets out of git; use env vars for all credentials.
