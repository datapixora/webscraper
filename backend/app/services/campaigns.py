from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic_campaign import CampaignStatus, TopicCampaign
from app.schemas.campaign import TopicCampaignCreate


class CampaignService:
    async def create(self, db: AsyncSession, payload: TopicCampaignCreate) -> TopicCampaign:
        campaign = TopicCampaign(
            name=payload.name,
            query=payload.query,
            seed_urls=[url.strip() for url in payload.seed_urls if url.strip()],
            allowed_domains=[d.strip() for d in payload.allowed_domains or [] if d.strip()] or None,
            max_pages=payload.max_pages,
            follow_links=payload.follow_links,
            status=CampaignStatus.ACTIVE,
            pages_collected=0,
            started_at=datetime.utcnow(),
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign

    async def list(self, db: AsyncSession) -> List[TopicCampaign]:
        result = await db.execute(select(TopicCampaign).order_by(TopicCampaign.created_at.desc()))
        return result.scalars().all()

    async def get(self, db: AsyncSession, campaign_id: str) -> Optional[TopicCampaign]:
        return await db.get(TopicCampaign, campaign_id)

    async def update_status(self, db: AsyncSession, campaign: TopicCampaign, status: CampaignStatus) -> TopicCampaign:
        campaign.status = status
        if status in {CampaignStatus.COMPLETED, CampaignStatus.FAILED, CampaignStatus.PAUSED}:
            campaign.finished_at = datetime.utcnow()
        await db.commit()
        await db.refresh(campaign)
        return campaign

    async def increment_pages(self, db: AsyncSession, campaign: TopicCampaign, count: int = 1) -> TopicCampaign:
        campaign.pages_collected += count
        if campaign.pages_collected >= campaign.max_pages:
            campaign.status = CampaignStatus.COMPLETED
            campaign.finished_at = datetime.utcnow()
        await db.commit()
        await db.refresh(campaign)
        return campaign

    async def get_page_count(self, db: AsyncSession, campaign_id: str) -> int:
        stmt = select(func.count()).select_from(TopicCampaign).join(TopicCampaign.pages).where(
            TopicCampaign.id == campaign_id
        )
        result = await db.execute(stmt)
        return int(result.scalar_one() or 0)


campaign_service = CampaignService()

__all__ = ["campaign_service", "CampaignService"]
