from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.topic_campaign import CampaignStatus
from app.schemas.campaign import (
    CrawledPageRead,
    TopicCampaignCreate,
    TopicCampaignRead,
    TopicCampaignUpdateStatus,
)
from app.services.campaigns import campaign_service
from app.services.crawled_pages import crawled_page_service
from app.workers.tasks import crawl_url, start_campaign

router = APIRouter()


@router.post("/", response_model=TopicCampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign(payload: TopicCampaignCreate, db: AsyncSession = Depends(get_db)) -> TopicCampaignRead:
    campaign = await campaign_service.create(db, payload)
    # kick off seeds
    start_campaign.delay(campaign.id)
    return TopicCampaignRead.model_validate(campaign)


@router.get("/", response_model=list[TopicCampaignRead])
async def list_campaigns(db: AsyncSession = Depends(get_db)) -> list[TopicCampaignRead]:
    campaigns = await campaign_service.list(db)
    return [TopicCampaignRead.model_validate(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=TopicCampaignRead)
async def get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)) -> TopicCampaignRead:
    campaign = await campaign_service.get(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return TopicCampaignRead.model_validate(campaign)


@router.get("/{campaign_id}/pages", response_model=list[CrawledPageRead])
async def list_campaign_pages(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
) -> list[CrawledPageRead]:
    campaign = await campaign_service.get(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    pages = await crawled_page_service.list_by_campaign(db, campaign_id, limit=limit, offset=offset, search=search)
    return [CrawledPageRead.model_validate(p) for p in pages]


@router.patch("/{campaign_id}/status", response_model=TopicCampaignRead)
async def update_campaign_status(
    campaign_id: str, payload: TopicCampaignUpdateStatus, db: AsyncSession = Depends(get_db)
) -> TopicCampaignRead:
    campaign = await campaign_service.get(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    updated = await campaign_service.update_status(db, campaign, payload.status)
    # If resuming from paused, restart seeds
    if payload.status == CampaignStatus.ACTIVE:
        start_campaign.delay(updated.id)
    return TopicCampaignRead.model_validate(updated)
