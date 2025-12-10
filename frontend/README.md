# WebScraper Frontend – Campaigns UI

## Pages
- `/campaigns`: list topic campaigns (name, status, pages_collected/max_pages) and create new ones.
- `/campaigns/[id]`: campaign detail with crawled pages table (search URL/text), page preview (title, text, raw HTML snippet).
- Existing pages: `/projects`, `/jobs`, `/dashboard`. Nav includes “Campaigns”.

## Create a campaign
Fields: name, query, seed URLs (one per line), optional allowed domains, max_pages, follow_links. Submit to auto-start the crawl.

## Data fetching
- API client adds: `getCampaigns`, `createCampaign`, `getCampaign`, `updateCampaignStatus`, `getCampaignPages`.
- Hooks: `useCampaigns`, `useCampaignPages`.
- Jobs page shows raw HTML metadata and download link (new jobs only).

## Dev
- App Router, React Query. API base from `NEXT_PUBLIC_API_BASE_URL` (fallback `NEXT_PUBLIC_API_URL` or `http://localhost:8000`).
- Run via Docker: `docker-compose up -d frontend` (host port 3002).
