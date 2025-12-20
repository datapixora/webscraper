import asyncio
import logging
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.crawled_page import PageStatus
from app.models.job import Job, JobStatus
from app.models.project import Project
from app.models.topic import Topic, TopicStatus
from app.models.topic_campaign import CampaignStatus, TopicCampaign
from app.models.topic_url import TopicURL
from app.schemas.result import ResultCreate
from app.scraper import crawl_page_for_campaign
from app.services.jobs import job_service
from app.services.results import result_service
from app.services.campaigns import campaign_service
from app.services.crawled_pages import crawled_page_service
from app.services.search_provider import search_provider, SearchResult
from app.services.topics import topic_service
from app.services.topic_urls import topic_url_service
from app.services.storage import storage_service
from app.services.exports import export_service
from app.services.export_generator import export_generator
from app.schemas.export import ExportCreate
from app.scraper import scrape_url
from app.workers.celery_app import celery_app
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@celery_app.task(name="health.ping")
def ping(message: str = "pong") -> dict[str, str]:
    """
    Simple task to verify the worker is alive.
    """
    return {"message": message}


@celery_app.task(
    name="jobs.run_scrape_job",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def run_scrape_job(job_id: str) -> dict[str, Any]:
    """
    Celery entrypoint: run a scrape job end-to-end.
    """

    async def _run() -> dict[str, Any]:
        async with AsyncSessionLocal() as db:
            job = await db.get(Job, job_id)
            if not job:
                logger.error("Job not found", extra={"job_id": job_id})
                return {"error": "job not found"}

            project_stmt = select(Project).where(Project.id == job.project_id)
            project_row = await db.execute(project_stmt)
            project = project_row.scalars().first()
            if not project:
                logger.error("Project not found", extra={"project_id": job.project_id})
                return {"error": "project not found"}

            # Start job
            await job_service.mark_started(db, job)

            # Validate URL against current project rules before scraping
            from app.services.url_validator import url_validator

            validation = await url_validator.validate_url(db, project, job.target_url, skip_dedup=True)
            if not validation.allowed:
                await job_service.mark_finished(
                    db, job, status=JobStatus.FAILED, error_message=validation.reason or "URL blocked"
                )
                return {"status": "blocked", "reason": validation.reason}

            try:
                # Use new scrape function with dynamic settings
                from app.scraper import scrape_url_with_settings

                scrape_result = await scrape_url_with_settings(
                    job.target_url, db, project.extraction_schema, job_id=job.id
                )

                blocked = scrape_result.get("blocked") or False
                block_reason = scrape_result.get("block_reason")
                http_status = scrape_result.get("http_status")
                method_used = scrape_result.get("method")

                storage_meta = storage_service.save_raw_html(
                    project_id=project.id, job_id=job.id, html=scrape_result["raw_html"]
                )
                preview = scrape_result["raw_html"][:4000]
                structured_data = scrape_result["structured_data"] or {}
                structured_data = {
                    **structured_data,
                    "_meta": {
                        "http_status": http_status,
                        "blocked": blocked,
                        "block_reason": block_reason,
                        "method_used": method_used,
                    },
                }

                result_payload = ResultCreate(
                    job_id=job.id,
                    project_id=project.id,
                    structured_data=structured_data,
                    raw_html=preview,
                    raw_html_path=storage_meta["path"],
                    raw_html_checksum=storage_meta["checksum"],
                    raw_html_size=storage_meta["size_bytes"],
                    raw_html_compressed_size=storage_meta["compressed_size_bytes"],
                    http_status=http_status,
                    blocked=blocked,
                    block_reason=block_reason,
                    method_used=method_used,
                )
                await result_service.upsert(db, payload=result_payload)

                if blocked:
                    await job_service.mark_finished(
                        db,
                        job,
                        status=JobStatus.BLOCKED,
                        error_message=block_reason or f"blocked (status {http_status})",
                    )
                    return {"status": "blocked", "reason": block_reason, "http_status": http_status}

                await job_service.mark_finished(db, job, status=JobStatus.SUCCEEDED, error_message=None)

                # Auto-export if enabled on project
                if project.auto_export_enabled:
                    export_payload = ExportCreate(
                        project_id=project.id,
                        topic_id=job.topic_id,
                        name=f"job-{job.id}",
                        format=(project.output_formats or ["jsonl"])[0],
                    )
                    export = await export_service.create(db, export_payload)
                    await export_generator.generate(db, export)

                return {"status": "ok", "job_id": job.id, "method": scrape_result["method"]}
            except Exception as exc:  # noqa: BLE001
                await job_service.mark_finished(db, job, status=JobStatus.FAILED, error_message=str(exc))
                logger.exception("Scrape job failed", extra={"job_id": job.id})
                return {"status": "error", "job_id": job.id, "error": str(exc)}

    return asyncio.run(_run())


@celery_app.task(name="campaigns.start_campaign")
def start_campaign(campaign_id: str) -> dict[str, Any]:
    async def _run() -> dict[str, Any]:
        async with AsyncSessionLocal() as db:
            campaign = await db.get(TopicCampaign, campaign_id)
            if not campaign:
                return {"error": "campaign not found"}
            if campaign.status not in {CampaignStatus.ACTIVE, CampaignStatus.PAUSED}:
                return {"status": "ignored"}

            # ensure status active
            if campaign.status == CampaignStatus.PAUSED:
                await campaign_service.update_status(db, campaign, CampaignStatus.ACTIVE)

            for seed in campaign.seed_urls:
                celery_app.send_task("campaigns.crawl_url", args=[campaign.id, seed, 0])
            return {"status": "started", "campaign_id": campaign.id, "seeds": len(campaign.seed_urls)}

    return asyncio.run(_run())


def _is_allowed(url: str, allowed_domains: list[str] | None) -> bool:
    if not allowed_domains:
        return True
    host = urlparse(url).hostname or ""
    return any(host.endswith(domain.strip()) for domain in allowed_domains)


@celery_app.task(name="campaigns.crawl_url")
def crawl_url(campaign_id: str, url: str, depth: int = 0) -> dict[str, Any]:
    async def _run() -> dict[str, Any]:
        url_clean = url.strip()
        async with AsyncSessionLocal() as db:
            campaign = await db.get(TopicCampaign, campaign_id)
            if not campaign:
                return {"error": "campaign not found"}
            if campaign.status != CampaignStatus.ACTIVE:
                return {"status": "skipped", "reason": "campaign not active"}

            if campaign.pages_collected >= campaign.max_pages:
                await campaign_service.update_status(db, campaign, CampaignStatus.COMPLETED)
                return {"status": "complete"}

            if await crawled_page_service.exists(db, campaign.id, url_clean):
                return {"status": "skipped", "reason": "duplicate"}

            crawl_result = await crawl_page_for_campaign(url_clean)
            status = (
                PageStatus.SUCCESS
                if crawl_result["http_status"] is not None and crawl_result["http_status"] < 400
                else PageStatus.FAILED
            )
            await crawled_page_service.create(
                db,
                campaign_id=campaign.id,
                url=url_clean,
                title=crawl_result["title"],
                raw_html=crawl_result["raw_html"],
                text_content=crawl_result["text_content"],
                http_status=crawl_result["http_status"],
                status=status,
            )

            if status == PageStatus.SUCCESS:
                await campaign_service.increment_pages(db, campaign, count=1)

            # Follow links if allowed and capacity remains
            if (
                status == PageStatus.SUCCESS
                and campaign.follow_links
                and campaign.status == CampaignStatus.ACTIVE
                and campaign.pages_collected < campaign.max_pages
            ):
                allowed = campaign.allowed_domains or []
                links = [link for link in crawl_result["links"] if _is_allowed(link, allowed)]
                # Cap enqueues to remaining budget
                remaining = campaign.max_pages - campaign.pages_collected
                enqueued = 0
                for link in links:
                    if enqueued >= remaining:
                        break
                    if not await crawled_page_service.exists(db, campaign.id, link):
                        celery_app.send_task("campaigns.crawl_url", args=[campaign.id, link, depth + 1])
                        enqueued += 1

            if campaign.pages_collected >= campaign.max_pages:
                await campaign_service.update_status(db, campaign, CampaignStatus.COMPLETED)

            return {"status": status.value, "url": url_clean}

    return asyncio.run(_run())


@celery_app.task(name="topics.run_topic_search")
def run_topic_search(topic_id: str) -> dict[str, Any]:
    async def _run() -> dict[str, Any]:
        async with AsyncSessionLocal() as db:
            topic = await db.get(Topic, topic_id)
            if not topic:
                return {"error": "topic not found"}
            await topic_service.update_status(db, topic, TopicStatus.SEARCHING)

            try:
                results: list[SearchResult] = await search_provider.search_web(topic.query, topic.max_results)
                rows = [
                    {
                        "url": r.url,
                        "title": r.title,
                        "snippet": r.snippet,
                        "rank": r.rank,
                    }
                    for r in results
                ]
                await topic_url_service.bulk_create(db, topic_id=topic.id, rows=rows)
                await topic_service.update_status(db, topic, TopicStatus.COMPLETED)
                return {"status": "ok", "count": len(rows)}
            except Exception as exc:  # noqa: BLE001
                await topic_service.update_status(db, topic, TopicStatus.FAILED)
                logger.exception("Topic search failed", extra={"topic_id": topic.id})
                return {"status": "error", "error": str(exc)}

    return asyncio.run(_run())
