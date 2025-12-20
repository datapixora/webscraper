import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.result import Result
from app.schemas.job import JobBatchCreate, JobRead
from app.schemas.result import ResultRead
from app.services.jobs import job_service
from app.services.results import result_service
from app.services.storage import storage_service
from app.services.projects import project_service
from app.workers.tasks import run_scrape_job

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[JobRead])
async def list_jobs(db: AsyncSession = Depends(get_db)) -> list[JobRead]:
    jobs = await job_service.list(db)
    return [JobRead.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobRead:
    job = await job_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobRead.model_validate(job)


@router.get("/{job_id}/results", response_model=ResultRead)
async def get_job_result(job_id: str, db: AsyncSession = Depends(get_db)) -> ResultRead:
    job = await job_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    result = await result_service.get_by_job(db, job_id)
    if not result:
        # Job exists but no result yet: return empty payload rather than 404 so UI can poll gracefully.
        return ResultRead.model_validate(
            {
                "id": job.id,
                "job_id": job.id,
                "project_id": job.project_id,
                "structured_data": {},
                "raw_html": None,
                "raw_html_path": None,
                "raw_html_checksum": None,
                "raw_html_size": None,
                "raw_html_compressed_size": None,
            }
        )
    return ResultRead.model_validate(result)


@router.get("/{job_id}/results/raw")
async def download_job_raw_html(job_id: str, db: AsyncSession = Depends(get_db)) -> Response:
    job = await job_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    result = await result_service.get_by_job(db, job_id)
    if not result or not result.raw_html_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw HTML not available")

    try:
        html = storage_service.fetch_raw_html(result.raw_html_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw HTML file missing")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load raw HTML")

    headers = {"Content-Disposition": f'attachment; filename="job-{job_id}.html"'}
    return Response(content=html, media_type="text/html; charset=utf-8", headers=headers)


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_jobs_batch(payload: JobBatchCreate, db: AsyncSession = Depends(get_db)):
    """
    Create multiple jobs for a project, applying project URL rules.
    Returns created jobs and rejected URLs with reasons.
    """
    # Support both new shape (jobs list) and legacy (project_id + urls)
    if payload.jobs:
        project_id = payload.jobs[0].project_id
        topic_id = payload.jobs[0].topic_id
        urls = [j.target_url for j in payload.jobs]
        name_prefix = payload.name_prefix or "Job"
        allow_duplicates = bool(payload.allow_duplicates)
    else:
        project_id = payload.project_id
        topic_id = payload.topic_id
        urls = payload.urls or []
        name_prefix = payload.name_prefix or "Job"
        allow_duplicates = bool(payload.allow_duplicates)

    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    created, rejected = await job_service.create_many_validated(
        db,
        project=project,
        urls=urls,
        topic_id=topic_id,
        name_prefix=name_prefix,
        skip_dedup=allow_duplicates,
    )

    logger.info(
        "jobs_created",
        extra={
            "project_id": project.id,
            "count": len(created),
            "rejected": len(rejected),
            "topic_id": payload.topic_id,
        },
    )

    for job in created:
        run_scrape_job.delay(job.id)

    return {
        "created": [JobRead.model_validate(j) for j in created],
        "rejected": [{"url": url, "reason": reason} for url, reason in rejected],
    }


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)) -> None:
    job = await job_service.get(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    await job_service.delete(db, job)
    return None
