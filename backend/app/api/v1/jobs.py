from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.result import Result
from app.schemas.job import JobRead
from app.schemas.result import ResultRead
from app.services.jobs import job_service
from app.services.results import result_service
from app.services.storage import storage_service

router = APIRouter()


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
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
