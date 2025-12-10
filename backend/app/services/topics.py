from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic, TopicStatus
from app.schemas.topic import TopicCreate


class TopicService:
    async def create(self, db: AsyncSession, payload: TopicCreate) -> Topic:
        topic = Topic(
            name=payload.name,
            query=payload.query,
            search_engine=payload.search_engine,
            max_results=payload.max_results,
            status=TopicStatus.PENDING,
        )
        db.add(topic)
        await db.commit()
        await db.refresh(topic)
        return topic

    async def list(self, db: AsyncSession) -> List[Topic]:
        res = await db.execute(select(Topic).order_by(Topic.created_at.desc()))
        return res.scalars().all()

    async def get(self, db: AsyncSession, topic_id: str) -> Optional[Topic]:
        return await db.get(Topic, topic_id)

    async def update_status(self, db: AsyncSession, topic: Topic, status: TopicStatus) -> Topic:
        topic.status = status
        await db.commit()
        await db.refresh(topic)
        return topic


topic_service = TopicService()

__all__ = ["topic_service", "TopicService"]
