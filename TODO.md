# TODO

- Add worker/beat + Redis to Render via blueprint once ready for background jobs.
- Wire Render Environment Groups for shared secrets and rotate `SECRET_KEY`.
- Add E2E test that hits `/health` and verifies DB via Playwright/API.
- Add CI job (or pre-push script) that runs `npm run dev:up`, hits `/health`, and tears down to guard regressions in the dev runner.
- Add integration test for `/health` ensuring degraded status when DB is unreachable.
- Consider optional flag in `scripts/dev.mjs` to skip `docker compose down` on exit for faster reload loops.
- Capture backend + frontend logs in docs/troubleshooting for common Windows/Docker Desktop issues.
- Add UI toast for job creation/logs when Celery enqueues to help debugging stuck jobs.
