from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.job import JobCreate, JobRead
from app.services.projects import project_service
from app.services.jobs import job_service
from app.workers.tasks import run_scrape_job

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
