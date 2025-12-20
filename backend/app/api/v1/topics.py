import json
import zipfile
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.topic import TopicStatus
from app.schemas.topic import TopicCreate, TopicRead, TopicURLRead
from app.schemas.job import JobCreate
from app.services.projects import project_service
from app.services.topic_urls import topic_url_service
from app.services.topics import topic_service
from app.services.jobs import job_service
from app.workers.tasks import run_topic_search, run_scrape_job
from app.services.url_validator import url_validator
from app.models.result import Result
from app.models.job import Job
from app.models.topic_url import TopicURL

router = APIRouter()


@router.post("/", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
async def create_topic(payload: TopicCreate, db: AsyncSession = Depends(get_db)) -> TopicRead:
    topic = await topic_service.create(db, payload)
    run_topic_search.delay(topic.id)
    return TopicRead.model_validate(topic)


@router.get("/", response_model=list[TopicRead])
async def list_topics(db: AsyncSession = Depends(get_db)) -> list[TopicRead]:
    topics = await topic_service.list(db)
    return [TopicRead.model_validate(t) for t in topics]


@router.get("/{topic_id}", response_model=TopicRead)
async def get_topic(topic_id: str, db: AsyncSession = Depends(get_db)) -> TopicRead:
    topic = await topic_service.get(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return TopicRead.model_validate(topic)


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(topic_id: str, db: AsyncSession = Depends(get_db)) -> None:
    topic = await topic_service.get(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    await topic_service.delete(db, topic)
    return None


@router.get("/{topic_id}/urls", response_model=list[TopicURLRead])
async def list_topic_urls(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    selected_for_scraping: bool | None = Query(default=None),
    scraped: bool | None = Query(default=None),
) -> list[TopicURLRead]:
    topic = await topic_service.get(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    urls = await topic_url_service.list(
        db, topic_id=topic_id, selected_for_scraping=selected_for_scraping, scraped=scraped
    )
    return [TopicURLRead.model_validate(u) for u in urls]


@router.patch("/{topic_id}/urls/select")
async def select_topic_urls(
    topic_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    url_ids = body.get("url_ids", [])
    selected = body.get("selected_for_scraping", True)
    topic = await topic_service.get(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    updated = await topic_url_service.update_selection(db, topic_id, url_ids, selected)
    return {"updated": updated}


@router.post("/{topic_id}/scrape-selected")
async def scrape_selected_topic_urls(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    body: dict | None = None,
):
    """
    Create scraping jobs for selected topic URLs.

    Requires a project_id in the request body to link jobs to a project.
    Jobs will also be linked to this topic for traceability.
    """
    topic = await topic_service.get(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    # Project ID is required so rules can be applied
    project_id = (body or {}).get("project_id")
    if not project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Default to allowing duplicates for manual sends; caller can disable by sending false
    allow_duplicates = (body or {}).get("allow_duplicates", True)

    urls = await topic_url_service.list(db, topic_id, selected_for_scraping=True, scraped=False)
    jobs_created = 0
    rejected: list[dict[str, str]] = []

    accepted_by_quota, rejected_pairs = await url_validator.enforce_quota(
        db, project, [turl.url for turl in urls]
    )
    for url, reason in rejected_pairs:
        rejected.append({"url": url, "reason": reason})

    for turl in urls:
        if turl.url not in accepted_by_quota:
            continue
        check = await url_validator.validate_url(db, project, turl.url, skip_dedup=allow_duplicates)
        if not check.allowed:
            rejected.append({"url": turl.url, "reason": check.reason or "not allowed"})
            continue
        payload = JobCreate(
            project_id=project.id,
            topic_id=topic_id,  # Link job to topic
            name=f"Topic scrape: {turl.url}",
            target_url=turl.url,
            scheduled_at=None,
            cron_expression=None,
        )
        job = await job_service.create(db, payload=payload)
        run_scrape_job.delay(job.id)
        turl.scraped = True
        db.add(turl)
        jobs_created += 1
    await db.commit()
    return {"jobs_created": jobs_created, "rejected": rejected}


@router.get("/{topic_id}/results/export")
async def export_topic_results(topic_id: str, db: AsyncSession = Depends(get_db)):
    topic = await topic_service.get(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    # load topic urls and normalize
    topic_urls = await topic_url_service.list(db, topic_id=topic_id)
    def _norm(url: str) -> str:
        return url.strip().rstrip("/").lower()

    normalized_targets = {_norm(tu.url) for tu in topic_urls if tu.url}

    results: list[Result] = []
    if normalized_targets:
        jobs_stmt = select(Job.id, Job.target_url).where(
            func.lower(func.trim(Job.target_url)).in_(normalized_targets)
        )
        job_rows = (await db.execute(jobs_stmt)).all()
        job_ids = [row.id for row in job_rows if _norm(row.target_url) in normalized_targets]

        if job_ids:
            stmt = select(Result).where(Result.job_id.in_(job_ids))
            results = (await db.execute(stmt)).scalars().all()

    memfile = BytesIO()
    with zipfile.ZipFile(memfile, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for res in results:
            payload = {
                "id": res.id,
                "job_id": res.job_id,
                "project_id": res.project_id,
                "structured_data": res.structured_data,
                "raw_html": res.raw_html,
                "raw_html_path": res.raw_html_path,
                "raw_html_checksum": res.raw_html_checksum,
                "raw_html_size": res.raw_html_size,
                "raw_html_compressed_size": res.raw_html_compressed_size,
                "created_at": res.created_at.isoformat() if res.created_at else None,
                "updated_at": res.updated_at.isoformat() if res.updated_at else None,
            }
            zf.writestr(f"result_{res.job_id}.json", json.dumps(payload, ensure_ascii=False, indent=2))

    memfile.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="topic_{topic_id}_results.zip"'}
    return StreamingResponse(memfile, media_type="application/zip", headers=headers)
