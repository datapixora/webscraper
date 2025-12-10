from __future__ import annotations

from typing import List, Optional, Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crawled_page import CrawledPage, PageStatus


class CrawledPageService:
    async def exists(self, db: AsyncSession, campaign_id: str, url: str) -> bool:
        stmt = select(func.count()).select_from(CrawledPage).where(
            and_(CrawledPage.campaign_id == campaign_id, CrawledPage.url == url)
        )
        res = await db.execute(stmt)
        return (res.scalar_one() or 0) > 0

    async def create(
        self,
        db: AsyncSession,
        *,
        campaign_id: str,
        url: str,
        title: Optional[str],
        raw_html: Optional[str],
        text_content: Optional[str],
        http_status: Optional[int],
        status: PageStatus,
    ) -> CrawledPage:
        page = CrawledPage(
            campaign_id=campaign_id,
            url=url,
            title=title,
            raw_html=raw_html,
            text_content=text_content,
            http_status=http_status,
            status=status,
        )
        db.add(page)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            existing = await db.execute(
                select(CrawledPage).where(and_(CrawledPage.campaign_id == campaign_id, CrawledPage.url == url))
            )
            found = existing.scalars().first()
            if found:
                return found
            raise
        await db.refresh(page)
        return page

    async def list_by_campaign(
        self,
        db: AsyncSession,
        campaign_id: str,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
    ) -> Sequence[CrawledPage]:
        stmt = select(CrawledPage).where(CrawledPage.campaign_id == campaign_id)
        if search:
            like = f"%{search}%"
            stmt = stmt.where((CrawledPage.url.ilike(like)) | (CrawledPage.text_content.ilike(like)))
        stmt = stmt.order_by(CrawledPage.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(stmt)
        return res.scalars().all()


crawled_page_service = CrawledPageService()

__all__ = ["crawled_page_service", "CrawledPageService"]
