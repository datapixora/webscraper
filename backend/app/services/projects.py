from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    async def create(self, db: AsyncSession, payload: ProjectCreate) -> Project:
        project = Project(
            name=payload.name,
            description=payload.description,
            extraction_schema=payload.extraction_schema,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    async def list(self, db: AsyncSession) -> list[Project]:
        result = await db.execute(select(Project).order_by(Project.created_at.desc()))
        return result.scalars().all()

    async def get(self, db: AsyncSession, project_id: str) -> Project | None:
        return await db.get(Project, project_id)

    async def update(self, db: AsyncSession, project: Project, payload: ProjectUpdate) -> Project:
        if payload.name is not None:
            project.name = payload.name
        if payload.description is not None:
            project.description = payload.description
        if payload.extraction_schema is not None:
            project.extraction_schema = payload.extraction_schema
        await db.commit()
        await db.refresh(project)
        return project


project_service = ProjectService()
