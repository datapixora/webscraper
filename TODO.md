# TODO

## Infrastructure
- Add worker/beat + Redis to Render via blueprint once ready for background jobs.
- Wire Render Environment Groups for shared secrets and rotate `SECRET_KEY`.
- Add E2E test that hits `/health` and verifies DB via Playwright/API.
- Add CI job (or pre-push script) that runs `npm run dev:up`, hits `/health`, and tears down to guard regressions in the dev runner.
- Add integration test for `/health` ensuring degraded status when DB is unreachable.
- Consider optional flag in `scripts/dev.mjs` to skip `docker compose down` on exit for faster reload loops.
- Capture backend + frontend logs in docs/troubleshooting for common Windows/Docker Desktop issues.
- Add UI toast for job creation/logs when Celery enqueues to help debugging stuck jobs.

## Proxy & Scraping (Recently Implemented)
✅ **Admin Proxy Settings UI + Backend Storage**
- Added advanced proxy configuration settings (rotation, sticky sessions, retries, delays)
- Implemented database-backed proxy settings with 60s cache (`proxy_manager.py`)
- Created `/api/v1/admin/settings/proxy` endpoint (GET/PUT)
- Added frontend UI in Settings page for advanced proxy configuration
- Worker now reads settings dynamically and applies:
  - Sticky sessions when enabled (configurable TTL)
  - Rotation strategies: per_job, on_failure, per_request
  - Automatic retry on 403/429/503 with configurable retry count
  - Request delays (random between min/max)
  - Scrape method policy (http/browser/auto) with auto-fallback
- Added `BLOCKED` job status for block detection
- Block detection includes status codes and content markers (Cloudflare, captcha, etc)

**Migration Required:**
- Run migration `0010_add_blocked_job_status.py` to add BLOCKED status to job_status enum

**Files Modified:**
- `backend/app/schemas/proxy_settings.py` (NEW)
- `backend/app/api/v1/admin_settings.py` (NEW)
- `backend/app/services/proxy_manager.py` (NEW)
- `backend/app/scraper.py` (enhanced with retry logic and dynamic settings)
- `backend/app/workers/tasks.py` (uses new scrape_url_with_settings)
- `backend/app/models/job.py` (added BLOCKED status)
- `frontend/src/app/settings/page.tsx` (added ProxySettings component)
- `frontend/src/hooks/useProxySettings.ts` (NEW)
