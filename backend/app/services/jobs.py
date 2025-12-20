from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.models.project import Project
from app.schemas.job import JobCreate, JobUpdate
from app.services.url_validator import url_validator


class JobService:
    async def create(self, db: AsyncSession, payload: JobCreate) -> Job:
        job = Job(
            project_id=payload.project_id,
            topic_id=payload.topic_id,
            name=payload.name,
            target_url=payload.target_url.strip(),
            scheduled_at=payload.scheduled_at,
            cron_expression=payload.cron_expression,
            status=JobStatus.PENDING,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def create_validated(
        self, db: AsyncSession, project: Project, payload: JobCreate, skip_dedup: bool = False
    ) -> Job:
        # Validate URL against project rules before creating
        url_check = await url_validator.validate_url(db, project, payload.target_url, skip_dedup=skip_dedup)
        if not url_check.allowed:
            raise ValueError(url_check.reason or "URL not allowed")
        return await self.create(db, payload)

    async def create_many_validated(
        self,
        db: AsyncSession,
        project: Project,
        urls: list[str],
        topic_id: str | None = None,
        name_prefix: str = "Job",
        skip_dedup: bool = False,
    ) -> tuple[list[Job], list[tuple[str, str]]]:
        """
        Create multiple jobs applying project rules. Returns (created_jobs, rejected[(url, reason)]).
        """
        cleaned = [u.strip() for u in urls if u and u.strip()]
        # Enforce per-run / total quotas first
        accepted_by_quota, rejected = await url_validator.enforce_quota(db, project, cleaned)

        created: list[Job] = []
        for url in accepted_by_quota:
            check = await url_validator.validate_url(db, project, url, skip_dedup=skip_dedup)
            if not check.allowed:
                rejected.append((url, check.reason or "not allowed"))
                continue
            job = Job(
                project_id=project.id,
                topic_id=topic_id,
                name=f"{name_prefix}: {url[:200]}",
                target_url=url,
                status=JobStatus.PENDING,
            )
            db.add(job)
            created.append(job)

        await db.commit()
        for job in created:
            await db.refresh(job)

        return created, rejected

    async def list_by_project(self, db: AsyncSession, project_id: str) -> list[Job]:
        result = await db.execute(
            select(Job).where(Job.project_id == project_id).order_by(Job.created_at.desc())
        )
        return result.scalars().all()

    async def list_by_project_and_statuses(
        self, db: AsyncSession, project_id: str, statuses: list[JobStatus]
    ) -> list[Job]:
        result = await db.execute(
            select(Job).where(Job.project_id == project_id, Job.status.in_(statuses)).order_by(Job.created_at.desc())
        )
        return result.scalars().all()

    async def list(self, db: AsyncSession) -> list[Job]:
        result = await db.execute(select(Job).order_by(Job.created_at.desc()))
        return result.scalars().all()

    async def get(self, db: AsyncSession, job_id: str) -> Job | None:
        return await db.get(Job, job_id)

    async def mark_started(self, db: AsyncSession, job: Job) -> Job:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        await db.commit()
        await db.refresh(job)
        return job

    async def mark_finished(
        self, db: AsyncSession, job: Job, status: JobStatus, error_message: str | None = None
    ) -> Job:
        job.status = status
        job.finished_at = datetime.utcnow()
        job.error_message = error_message
        await db.commit()
        await db.refresh(job)
        return job

    async def update(self, db: AsyncSession, job: Job, payload: JobUpdate) -> Job:
        if payload.status is not None:
            job.status = payload.status
        if payload.started_at is not None:
            job.started_at = payload.started_at
        if payload.finished_at is not None:
            job.finished_at = payload.finished_at
        if payload.error_message is not None:
            job.error_message = payload.error_message
        await db.commit()
        await db.refresh(job)
        return job

    async def delete(self, db: AsyncSession, job: Job) -> None:
        await db.delete(job)
        await db.commit()


job_service = JobService()
