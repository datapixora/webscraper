# WebScraper SaaS – Current State (2025-12-10)

## Overview
- Full FastAPI backend with Projects, Jobs, Results, Topic Campaigns (auto-crawl), and Topic URL discovery via web search; Celery workers handle scraping and searches.
- Next.js 14 dashboard wired to backend APIs (Projects, Jobs, Campaigns, Topics) with React Query and live data.
- Scraping engine uses httpx + Playwright; search provider defaults to DuckDuckGo HTML scraping with a Mock fallback.

## Key Backend Pieces
- Models & migrations: Topic, TopicURL (discovered URLs) plus Campaign/CrawledPage (auto-crawl). Migration `0004_add_topics.py` adds Topic/TopicURL tables.
- Services: `search_provider.py` (DuckDuckGo or mock), `topics.py`, `topic_urls.py`, `projects.ensure_default_topic_project`.
- Tasks: `run_topic_search` (collect URLs), existing `run_scrape_job` for scraping; NullPool avoids async loop issues in worker/beat/frontend settings.
- Routes: `/api/v1/topics` with create/list/detail, URLs listing, selection toggle, and `scrape-selected` to spawn Jobs from chosen URLs.

## Key Frontend Pieces
- Dashboard (`/dashboard`) now live: shows real counts for Projects, Jobs (by status), Campaigns, Topics, plus recent jobs table and discovery snapshot.
- Topics: `/topics` list + creation (choose DuckDuckGo or Mock); `/topics/[id]` shows discovered URLs with checkboxes and “Create scraping jobs for selected”.
- Campaigns: `/campaigns` list/create; Projects and Jobs pages wired to backend; JSON viewer for results.
- API client (`src/lib/api-client.ts`) exposes typed methods for projects/jobs/results/campaigns/topics/topic URLs.

## How to Run
```
docker-compose up -d
```
- Frontend: http://localhost:3002 (mapped from 3000).
- Backend: http://localhost:8000 (docs at /docs).
- Worker/Beat/Flower started via compose; Postgres/Redis included.

## How to Use
- Projects: create with extraction schema; create Jobs per project and view statuses.
- Topics (URL discovery):
  1) Go to `/topics`, create a topic; keep “DuckDuckGo (live)” for real results (Mock returns 3 sample URLs).
  2) Open a topic (View URLs), select checkboxes, click “Create scraping jobs for selected”. Jobs appear on `/jobs`.
- Campaigns (auto-crawl): create campaign with seeds, allowed domains, max pages; crawling runs via Celery and pages collected are visible on campaign detail page.

## Notes / Next Steps
- For real search results ensure outbound network is allowed; set `SEARCH_PROVIDER=duckduckgo` (default) or `SEARCH_PROVIDER=mock` to force mock.
- To push to GitHub, run: `git add . && git commit -m "Add topics discovery + live dashboard" && git push origin main` (credentials required).
