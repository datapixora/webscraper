from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductService:
    async def upsert(
        self,
        db: AsyncSession,
        *,
        domain: str,
        project_id: str | None,
        url: str,
        title: Optional[str],
        price_text: Optional[str],
        images: list[str],
        categories: list[str],
        tags: list[str],
        specs: list[str],
        description_html: Optional[str],
        sku: Optional[str],
        raw_json: dict[str, Any] | None = None,
    ) -> Product:
        stmt = select(Product).where(Product.url == url)
        existing = (await db.execute(stmt)).scalars().first()
        if existing:
            existing.title = title
            existing.price_text = price_text
            existing.images_json = {"items": images}
            existing.categories_json = {"items": categories}
            existing.tags_json = {"items": tags}
            existing.description_html = description_html
            existing.sku = sku
            existing.raw_json = raw_json
            existing.project_id = project_id
            product = existing
        else:
            product = Product(
                project_id=project_id,
                domain=domain,
                url=url,
                title=title,
                price_text=price_text,
                images_json={"items": images},
                categories_json={"items": categories},
                tags_json={"items": tags},
                description_html=description_html,
                sku=sku,
                raw_json=raw_json,
            )
            db.add(product)

        await db.commit()
        await db.refresh(product)
        return product

    async def list_by_domain(
        self, db: AsyncSession, domain: str, project_id: str | None = None, limit: int = 1000, offset: int = 0
    ) -> list[Product]:
        stmt = select(Product).where(Product.domain == domain)
        if project_id:
            stmt = stmt.where(Product.project_id == project_id)
        stmt = stmt.order_by(Product.created_at.desc()).limit(limit).offset(offset)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())


product_service = ProductService()

__all__ = ["product_service", "ProductService"]
