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
        # Persist all configurable fields so defaults from the schema are saved in the DB.
        project = Project(**payload.model_dump())
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
        # Only apply fields provided by the client.
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await db.commit()
        await db.refresh(project)
        return project

    async def delete(self, db: AsyncSession, project: Project) -> None:
        await db.delete(project)
        await db.commit()


project_service = ProjectService()
