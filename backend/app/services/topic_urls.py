from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic_url import TopicURL


class TopicURLService:
    async def bulk_create(
        self,
        db: AsyncSession,
        topic_id: str,
        rows: Iterable[dict],
    ) -> List[TopicURL]:
        created: list[TopicURL] = []
        for row in rows:
            url = TopicURL(
                topic_id=topic_id,
                url=row.get("url", ""),
                title=row.get("title"),
                snippet=row.get("snippet"),
                rank=row.get("rank"),
            )
            db.add(url)
            created.append(url)
        await db.commit()
        for c in created:
            await db.refresh(c)
        return created

    async def list(
        self,
        db: AsyncSession,
        topic_id: str,
        selected_for_scraping: Optional[bool] = None,
        scraped: Optional[bool] = None,
    ) -> Sequence[TopicURL]:
        stmt = select(TopicURL).where(TopicURL.topic_id == topic_id)
        if selected_for_scraping is not None:
            stmt = stmt.where(TopicURL.selected_for_scraping == selected_for_scraping)
        if scraped is not None:
            stmt = stmt.where(TopicURL.scraped == scraped)
        stmt = stmt.order_by(TopicURL.rank.asc().nullslast(), TopicURL.created_at.asc())
        res = await db.execute(stmt)
        return res.scalars().all()

    async def update_selection(
        self, db: AsyncSession, topic_id: str, url_ids: list[str], selected: bool
    ) -> int:
        stmt = (
            update(TopicURL)
            .where(and_(TopicURL.topic_id == topic_id, TopicURL.id.in_(url_ids)))
            .values(selected_for_scraping=selected)
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount or 0


topic_url_service = TopicURLService()

__all__ = ["topic_url_service", "TopicURLService"]
