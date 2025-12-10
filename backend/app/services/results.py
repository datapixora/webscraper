from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.result import Result
from app.schemas.result import ResultCreate


class ResultService:
    async def upsert(self, db: AsyncSession, payload: ResultCreate) -> Result:
        existing = await db.execute(select(Result).where(Result.job_id == payload.job_id))
        result = existing.scalars().first()

        if result:
            result.structured_data = payload.structured_data
            result.raw_html = payload.raw_html
            result.raw_html_path = payload.raw_html_path
            result.raw_html_checksum = payload.raw_html_checksum
            result.raw_html_size = payload.raw_html_size
            result.raw_html_compressed_size = payload.raw_html_compressed_size
        else:
            result = Result(
                job_id=payload.job_id,
                project_id=payload.project_id,
                structured_data=payload.structured_data,
                raw_html=payload.raw_html,
                raw_html_path=payload.raw_html_path,
                raw_html_checksum=payload.raw_html_checksum,
                raw_html_size=payload.raw_html_size,
                raw_html_compressed_size=payload.raw_html_compressed_size,
            )
            db.add(result)

        await db.commit()
        await db.refresh(result)
        return result

    async def get_by_job(self, db: AsyncSession, job_id: str) -> Result | None:
        existing = await db.execute(select(Result).where(Result.job_id == job_id))
        return existing.scalars().first()


result_service = ResultService()
