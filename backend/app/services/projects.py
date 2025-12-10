from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    async def ensure_default_topic_project(self, db: AsyncSession, topic) -> Project:
        """
        Ensure a default project exists for topic-derived scrapes.
        """
        name = f"Topic: {topic.name}"
        existing = await db.execute(select(Project).where(Project.name == name))
        proj = existing.scalars().first()
        if proj:
            return proj
        payload = ProjectCreate(name=name, description=f"Auto-created for topic {topic.name}", extraction_schema=None)
        return await self.create(db, payload)

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
