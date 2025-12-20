from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from celery import current_app as celery_app

from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.job import JobCreate, JobRead
from app.services.projects import project_service
from app.services.jobs import job_service
from app.workers.tasks import run_scrape_job
from app.models.job import JobStatus

router = APIRouter()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)) -> ProjectRead:
    project = await project_service.create(db, payload)
    return ProjectRead.model_validate(project)


@router.get("/", response_model=list[ProjectRead])
async def list_projects(db: AsyncSession = Depends(get_db)) -> list[ProjectRead]:
    projects = await project_service.list(db)
    return [ProjectRead.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)) -> ProjectRead:
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)
) -> ProjectRead:
    """
    Partially update a project with any subset of fields.
    """
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project = await project_service.update(db, project, payload)
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/pause", response_model=ProjectRead)
async def pause_project(project_id: str, payload: dict, db: AsyncSession = Depends(get_db)) -> ProjectRead:
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    paused = bool(payload.get("paused"))
    project = await project_service.set_pause(db, project, paused=paused)
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/stop")
async def stop_project(project_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    project = await project_service.set_pause(db, project, paused=True)
    running_jobs = await job_service.list_by_project_and_statuses(
        db, project_id=project_id, statuses=[JobStatus.RUNNING, JobStatus.PENDING, JobStatus.QUEUED]
    )
    revoked = 0
    for job in running_jobs:
        if job.celery_task_id:
            try:
                celery_app.control.revoke(job.celery_task_id, terminate=False)
                revoked += 1
            except Exception:
                pass
        job.status = JobStatus.CANCELLED
    await db.commit()
    return {"revoked": revoked, "cancelled": len(running_jobs)}


@router.delete("/{project_id}/purge")
async def purge_project(project_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await stop_project(project_id, db)
    await db.execute(sa.text("DELETE FROM products WHERE project_id=:pid"), {"pid": project_id})
    await db.execute(sa.text("DELETE FROM results WHERE project_id=:pid"), {"pid": project_id})
    await db.execute(sa.text("DELETE FROM jobs WHERE project_id=:pid"), {"pid": project_id})
    await db.commit()
    return {"purged": True}


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)) -> None:
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await project_service.delete(db, project)
    return None


@router.post("/{project_id}/jobs", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job_for_project(
    project_id: str, payload: JobCreate, db: AsyncSession = Depends(get_db)
) -> JobRead:
    if project_id != payload.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="project_id mismatch in payload"
        )
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    try:
        job = await job_service.create_validated(db, project, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Trigger Celery task asynchronously
    run_scrape_job.delay(job.id)
    return JobRead.model_validate(job)
