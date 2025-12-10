from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.topic import TopicStatus
from app.schemas.base import Identified


class TopicCreate(BaseModel):
    name: str = Field(..., max_length=255)
    query: str = Field(..., max_length=512)
    search_engine: str = Field(default="mock", max_length=50)
    max_results: int = Field(default=20, ge=1, le=100)


class TopicRead(Identified):
    name: str
    query: str
    search_engine: str
    max_results: int
    status: TopicStatus


class TopicURLRead(Identified):
    topic_id: str
    url: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    rank: Optional[int] = None
    selected_for_scraping: bool
    scraped: bool
