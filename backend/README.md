# WebScraper Backend – Topic Campaigns & Auto-Crawl

## What’s new
- **TopicCampaign / CrawledPage models** with enums for campaign and page status.
- **Alembic migration** `0003_add_topic_campaigns.py` creates the new tables.
- **Celery tasks** `campaigns.start_campaign` and `campaigns.crawl_url` to enqueue seeds and crawl/follow links up to `max_pages`, respecting `allowed_domains` and deduping URLs.
- **Scraper helper** `crawl_page_for_campaign` extracts title, text, links, and status.
- **API endpoints** under `/api/v1/campaigns`:
  - `POST /api/v1/campaigns` create + auto-start
  - `GET /api/v1/campaigns` list
  - `GET /api/v1/campaigns/{id}` detail
  - `GET /api/v1/campaigns/{id}/pages` list pages (limit/offset/search)
  - `PATCH /api/v1/campaigns/{id}/status` pause/resume
- **Storage**: raw HTML persisted via storage service (local or S3). Jobs UI shows path/checksum/size and has a download endpoint `GET /api/v1/jobs/{id}/results/raw`.

## How it runs
1) Bring services up: `docker-compose up -d backend worker beat frontend`.
2) Create a campaign (UI or API):
   - name, query, seed_urls (list), optional allowed_domains, max_pages, follow_links.
   - seeds enqueue automatically via Celery (`campaigns.start_campaign`).
3) Worker crawls pages (`campaigns.crawl_url`):
   - fetch, extract title/text, save `CrawledPage`, increment `pages_collected`.
   - if `follow_links` and under `max_pages`, enqueue in-domain links.
   - status transitions to `completed` when `pages_collected >= max_pages`.
4) View results:
   - UI: `/campaigns` (list/create), `/campaigns/{id}` (pages table, search, preview).
   - API: `/api/v1/campaigns/{id}/pages`.
   - Raw HTML download for jobs: `/api/v1/jobs/{id}/results/raw`.

## Env/config notes
- Storage: default local (`STORAGE_BACKEND=local`, `STORAGE_LOCAL_PATH=./storage`). For S3/MinIO set `STORAGE_BACKEND=s3` and `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`, `AWS_S3_REGION` (optionally `AWS_S3_ENDPOINT_URL`), then recreate backend/worker/beat.
- Playwright/http timeouts: `PLAYWRIGHT_TIMEOUT`, `DEFAULT_TIMEOUT`.

## Frontend (Next.js 14)
- Routes: `/campaigns` (list/create), `/campaigns/[id]` (detail, page list, search, preview). Nav includes Campaigns.
- Hooks/API client: `useCampaigns`, `useCampaignPages`, and `get/create/getById/getPages/updateStatus` functions in `src/lib/api-client.ts`.
