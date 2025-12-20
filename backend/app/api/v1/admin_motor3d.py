from __future__ import annotations

import asyncio
import httpx
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.domain_policy import DomainPolicy
from app.schemas.motor3d import (
    Motor3DCreateJobsRequest,
    Motor3DCreateJobsResponse,
    Motor3DDiscoverRequest,
    Motor3DDiscoverResponse,
    Motor3DParseRequest,
    Motor3DProduct,
)
from app.services.domain_policy import domain_policy_service
from app.services.jobs import job_service
from app.services.products import product_service
from app.services.projects import project_service
from app.scraper import scrape_url_with_settings

router = APIRouter()


async def _fetch_xml(url: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def _parse_sitemap(xml_text: str) -> list[str]:
    tree = ET.fromstring(xml_text)
    locs: list[str] = []
    for loc in tree.iter("{*}loc"):
        if loc.text:
            locs.append(loc.text.strip())
    return locs


@router.post("/discover", response_model=Motor3DDiscoverResponse)
async def discover_products(payload: Motor3DDiscoverRequest) -> Motor3DDiscoverResponse:
    seen: set[str] = set()
    to_visit = [payload.sitemap_url]

    while to_visit and len(seen) < payload.limit:
        current = to_visit.pop()
        try:
            xml_text = await _fetch_xml(current)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
        locs = _parse_sitemap(xml_text)
        for loc in locs:
            if loc.endswith(".xml"):
                to_visit.append(loc)
                continue
            if loc.startswith(payload.url_prefix):
                seen.add(loc)
            if len(seen) >= payload.limit:
                break

    urls = sorted(seen)
    return Motor3DDiscoverResponse(count=len(urls), urls=urls[: min(len(urls), 5000)])


@router.post("/create-jobs", response_model=Motor3DCreateJobsResponse)
async def create_jobs(payload: Motor3DCreateJobsRequest, db: AsyncSession = Depends(get_db)) -> Motor3DCreateJobsResponse:
    project = await project_service.get(db, payload.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Ensure policy exists with defaults
    existing_policy = await domain_policy_service.get_by_domain(db, payload.policy_domain)
    if not existing_policy:
        await domain_policy_service.create(
            db,
            domain=payload.policy_domain,
            enabled=True,
            method="http",
            use_proxy=False,
            request_delay_ms=1000,
            max_concurrency=1,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            block_resources=True,
        )

    created, rejected = await job_service.create_many_validated(
        db,
        project,
        urls=payload.urls,
        topic_id=None,
        name_prefix=payload.name_prefix,
        skip_dedup=payload.allow_duplicates,
    )
    return Motor3DCreateJobsResponse(
        created=len(created),
        rejected=[{"url": url, "reason": reason} for url, reason in rejected],
    )


def _parse_product(html: str) -> Motor3DProduct:
    soup = BeautifulSoup(html, "html.parser")
    title = None
    price_text = None
    sku = None

    title_tag = soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)

    price_tag = soup.select_one(".price") or soup.select_one("[itemprop=price]")
    if price_tag:
        price_text = price_tag.get_text(" ", strip=True)

    sku_tag = soup.select_one(".sku")
    if sku_tag:
        sku = sku_tag.get_text(strip=True)

    images = []
    for img in soup.select("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            images.append(src)

    categories = [a.get_text(strip=True) for a in soup.select(".posted_in a")]
    tags = [a.get_text(strip=True) for a in soup.select(".tagged_as a")]

    desc_block = soup.select_one(".woocommerce-product-details__short-description") or soup.select_one(".product-content")
    description_html = desc_block.decode_contents() if desc_block else None

    return Motor3DProduct(
        url="",
        title=title,
        price_text=price_text,
        images=images,
        categories=categories,
        tags=tags,
        description_html=description_html,
        sku=sku,
        raw={},
    )


@router.post("/parse", response_model=Motor3DProduct)
async def parse_product(payload: Motor3DParseRequest, db: AsyncSession = Depends(get_db)) -> Motor3DProduct:
    try:
        scrape = await scrape_url_with_settings(
            url=str(payload.url),
            db=db,
            extraction_schema=None,
            force_method="httpx" if payload.method == "http" else None,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    product = _parse_product(scrape["raw_html"])
    product.url = str(payload.url)
    product.raw = {
        "http_status": scrape.get("http_status"),
        "blocked": scrape.get("blocked"),
        "block_reason": scrape.get("block_reason"),
        "method": scrape.get("method"),
    }

    # persist
    await product_service.upsert(
        db,
        domain=urlparse(str(payload.url)).hostname or "",
        url=str(payload.url),
        title=product.title,
        price_text=product.price_text,
        images=product.images,
        categories=product.categories,
        tags=product.tags,
        description_html=product.description_html,
        sku=product.sku,
        raw_json=product.raw,
    )

    return product


@router.get("/products", response_model=list[Motor3DProduct])
async def list_products(db: AsyncSession = Depends(get_db)) -> list[Motor3DProduct]:
    products = await product_service.list_by_domain(db, domain="motor3dmodel.ir", limit=200)
    output: list[Motor3DProduct] = []
    for p in products:
        output.append(
            Motor3DProduct(
                url=p.url,
                title=p.title,
                price_text=p.price_text,
                images=p.images_json.get("items", []) if p.images_json else [],
                categories=p.categories_json.get("items", []) if p.categories_json else [],
                tags=p.tags_json.get("items", []) if p.tags_json else [],
                description_html=p.description_html,
                sku=p.sku,
                raw=p.raw_json or {},
            )
        )
    return output
