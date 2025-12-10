from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.crawled_page import PageStatus
from app.models.topic_campaign import CampaignStatus
from app.schemas.base import Identified


class TopicCampaignCreate(BaseModel):
    name: str = Field(..., max_length=255)
    query: str = Field(..., max_length=512)
    seed_urls: List[str]
    allowed_domains: Optional[List[str]] = None
    max_pages: int = Field(default=50, ge=1, le=5000)
    follow_links: bool = True


class TopicCampaignRead(Identified):
    name: str
    query: str
    seed_urls: List[str]
    allowed_domains: Optional[List[str]] = None
    max_pages: int
    pages_collected: int
    follow_links: bool
    status: CampaignStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class CrawledPageRead(Identified):
    campaign_id: str
    url: str
    title: Optional[str]
    raw_html: Optional[str]
    text_content: Optional[str]
    http_status: Optional[int]
    status: PageStatus


class TopicCampaignUpdateStatus(BaseModel):
    status: CampaignStatus
