# WebScraper Platform

Production-ready scaffolding for a full-stack web scraping platform with a modern admin dashboard, robust API, and scheduled scraping jobs.

## Features
- Intelligent scraping: Playwright for JavaScript-heavy sites plus fast HTML parsing
- Multi-tenant projects with isolation
- Flexible scheduling: one-time, cron, hourly, daily, weekly
- Extraction schemas: CSS selectors, XPath, JSONPath
- Monitoring: job status, success rates, performance metrics
- Webhooks on completion
- Proxy rotation and rate limiting
- Result export: JSON and CSV via API

## Architecture
- Frontend: Next.js 14 (App Router), React 18, Tailwind CSS
- Backend: FastAPI API, Celery workers, PostgreSQL, Redis
- Scraping: Playwright browser automation plus HTML parsers
- Orchestration: Docker Compose for dev; separate services for API, worker, beat, Flower, Redis, Postgres

## Tech Stack
- Backend: Python 3.11, FastAPI, SQLAlchemy, Alembic, Celery, Redis, Playwright
- Frontend: Next.js, TypeScript, Tailwind CSS, TanStack Query, Zustand, Recharts
- DevOps: Docker, Docker Compose, Flower for Celery monitoring, structured logging

## Status
This repository currently contains configuration scaffolding only. Application code for `backend/app` and `frontend/src` is not yet included. Add your API, models, workers, and frontend pages/components to make the stack runnable.

## Project Structure
```
webscraper/
├─ backend/           # FastAPI backend (code not yet present)
├─ frontend/          # Next.js frontend (code not yet present)
├─ docker-compose.yml # Dev orchestration
├─ Makefile           # Helper commands
└─ .env.example       # Environment template
```

## Getting Started
Prerequisites: Docker and Docker Compose; Make (optional).

1) Copy environment template  
```bash
make create-env   # or: cp .env.example .env
```
2) Update `.env` with secrets (e.g., `SECRET_KEY`, database password) and CORS origins.  
3) Build and start  
```bash
make init
# or manually:
docker-compose up -d
```
4) When code is added and services are running:  
- Frontend: http://localhost:3000  
- Backend: http://localhost:8000  
- API Docs (Swagger): http://localhost:8000/docs  
- Flower: http://localhost:5555

## Useful Commands (Makefile)
- `make dev` — start all services with logs
- `make up` / `make down` — start/stop in background
- `make logs` / `make logs-backend` / `make logs-worker` — follow logs
- `make migrate` / `make migrate-create MESSAGE="desc"` — Alembic migrations
- `make seed` — seed sample data (requires your seed script)
- `make test` / `make test-backend` / `make test-frontend` — run tests
- `make format` / `make lint` — code quality helpers

## Environment
See `.env.example` for full variables (DB/Redis URLs, auth, scraping, proxies, Celery, logging, feature flags). In production, set strong secrets, enable HTTPS, and tune rate limits/proxy settings.

## Deployment Notes
- Build production images: `make build-prod`
- Start production stack: `make up-prod` (expects a `docker-compose.prod.yml` you provide)
- Run migrations before releasing: `alembic upgrade head`

## Contributing
1. Fork and create a feature branch.  
2. Add backend code under `backend/app/...` and frontend code under `frontend/src/...`.  
3. Run `make format` and `make lint`.  
4. Open a PR.

## Support
- Issues: https://github.com/yourusername/webscraper/issues
- Discussions: https://github.com/yourusername/webscraper/discussions
- Email: support@webscraper.com
