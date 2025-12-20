from __future__ import annotations

import asyncio
import httpx
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.connectors.motor3d import discover_product_urls
from app.schemas.motor3d import (
    Motor3DCreateJobsRequest,
    Motor3DCreateJobsResponse,
    Motor3DDiscoverRequest,
    Motor3DDiscoverResponse,
    Motor3DParseRequest,
    Motor3DProduct,
    Motor3DRunRequest,
    Motor3DRunResponse,
)
from app.services.domain_policy import domain_policy_service
from app.services.jobs import job_service
from app.services.products import product_service
from app.services.projects import project_service
from app.scraper import scrape_url_with_settings
from app.services.proxy_config import get_httpx_proxy_dict
from app.core.config import settings
import logging
from urllib.parse import urlparse
from app.workers.tasks import run_scrape_job

logger = logging.getLogger(__name__)


def _parse_motor3d_product(html: str, url: str) -> Motor3DProduct:
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title = None
    title_tag = soup.select_one("h1.product_title") or soup.select_one("h1.entry-title") or soup.find("h1")
    if title_tag:
        title = title_tag.get_text(" ", strip=True)

    # Price
    price_text = None
    price_tag = soup.select_one(".summary .price") or soup.select_one(".price")
    if price_tag:
        price_text = price_tag.get_text(" ", strip=True)
    else:
        # Fallback: look for تومان near dynamic fields
        for span in soup.select(".jet-listing-dynamic-field__content"):
            txt = span.get_text(" ", strip=True)
            if "تومان" in txt:
                price_text = txt
                break

    # Specs / features
    specs = [
        s.get_text(" ", strip=True)
        for s in soup.select(".jet-listing-dynamic-repeater__item span")
        if s.get_text(strip=True)
    ]

    # Images
    images = []
    for img in soup.select(".woocommerce-product-gallery img"):
        src = img.get("data-src") or img.get("src")
        if src:
            images.append(src)
    if not images:
        for img in soup.find_all("img"):
            src = img.get("data-src") or img.get("src")
            if not src:
                continue
            if "wp-content/uploads" in src and all(
                ban not in src for ban in ["MainLogo.webp", "s.w.org", "zarinpal", "enamad"]
            ):
                images.append(src)

    # Categories / tags
    categories = [a.get_text(" ", strip=True) for a in soup.select(".posted_in a")]
    tags = [a.get_text(" ", strip=True) for a in soup.select(".tagged_as a")]

    description_html = None
    desc_block = soup.select_one(".woocommerce-product-details__short-description") or soup.select_one(
        ".product-content"
    )
    if desc_block:
        description_html = desc_block.decode_contents()

    sku = None
    sku_tag = soup.select_one(".sku")
    if sku_tag:
        sku = sku_tag.get_text(strip=True)

    return Motor3DProduct(
        url=url,
        title=title,
        price_text=price_text,
        images=images,
        specs=specs,
        categories=categories,
        tags=tags,
        description_html=description_html,
        sku=sku,
        raw={},
    )

router = APIRouter()


def _parse_sitemap(xml_text: str) -> list[str]:
    tree = ET.fromstring(xml_text)
    locs: list[str] = []
    for loc in tree.iter("{*}loc"):
        if loc.text:
            locs.append(loc.text.strip())
    return locs


async def _make_client(use_proxy: bool, user_agent: str | None) -> httpx.AsyncClient:
    headers = {"User-Agent": user_agent or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    proxies = get_httpx_proxy_dict() if use_proxy else None
    return httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True, proxies=proxies)


async def _fetch_xml(client: httpx.AsyncClient, url: str) -> str:
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.text


@router.post("/discover", response_model=Motor3DDiscoverResponse)
async def discover_products(payload: Motor3DDiscoverRequest, db: AsyncSession = Depends(get_db)) -> Motor3DDiscoverResponse:
    domain = payload.domain or "motor3dmodel.ir"
    base = domain.replace("https://", "").replace("http://", "").strip("/")
    sitemap_url = payload.sitemap_url or f"https://{base}/wp-sitemap.xml"
    url_prefix = payload.url_prefix or f"https://{base}/product/"

    policy = await domain_policy_service.get_by_domain(db, base)
    if not policy:
        policy = await domain_policy_service.create(
            db,
            domain=base,
            enabled=True,
            method="http",
            use_proxy=False,
            request_delay_ms=1000,
            max_concurrency=1,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            block_resources=True,
        )

    try:
        urls = await discover_product_urls(
            domain=base,
            sitemap_url=sitemap_url,
            url_prefix=url_prefix,
            policy=policy,
            max_urls=payload.max_urls,
        )
    except ValueError as ve:
        logger.exception("motor3d discover failed", extra={"domain": base})
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=str(ve)[:200],
        ) from ve
    except Exception as exc:  # noqa: BLE001
        logger.exception("motor3d discover failed", extra={"domain": base})
        detail = "motor3d discover failed; see server logs"
        if settings.environment == "development":
            detail = f"{detail}: {str(exc)[:200]}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc

    sample = urls[: min(len(urls), 20)]
    return Motor3DDiscoverResponse(count=len(urls), sample_urls=sample, urls=urls)


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
        job_ids=[j.id for j in created],
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

    product = _parse_motor3d_product(scrape["raw_html"], str(payload.url))
    product.raw = {
        "http_status": scrape.get("http_status"),
        "blocked": scrape.get("blocked"),
        "block_reason": scrape.get("block_reason"),
        "method": scrape.get("method"),
        "specs": product.specs,
    }

    # persist
    await product_service.upsert(
        db,
        domain=urlparse(str(payload.url)).hostname or "",
        project_id=payload.project_id if hasattr(payload, "project_id") else None,
        url=str(payload.url),
        title=product.title,
        price_text=product.price_text,
        images=product.images,
        categories=product.categories,
        tags=product.tags,
        specs=product.specs,
        description_html=product.description_html,
        sku=product.sku,
        raw_json=product.raw,
    )

    return product


@router.get("/products", response_model=list[Motor3DProduct])
async def list_products(db: AsyncSession = Depends(get_db)) -> list[Motor3DProduct]:
    products = await product_service.list_by_domain(db, domain="motor3dmodel.ir", project_id=None, limit=200)
    output: list[Motor3DProduct] = []
    for p in products:
        output.append(
            Motor3DProduct(
                url=p.url,
                title=p.title,
                price_text=p.price_text,
                images=p.images_json.get("items", []) if p.images_json else [],
                specs=(p.raw_json or {}).get("specs", []),
                categories=p.categories_json.get("items", []) if p.categories_json else [],
                tags=p.tags_json.get("items", []) if p.tags_json else [],
                description_html=p.description_html,
                sku=p.sku,
                raw=p.raw_json or {},
            )
        )
    return output


@router.get("/export-csv")
async def export_csv(project_id: str | None = None, db: AsyncSession = Depends(get_db)):
    products = await product_service.list_by_domain(
        db, domain="motor3dmodel.ir", project_id=project_id, limit=5000
    )
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["url", "title", "price_text", "specs", "images_first", "images_all"])
    for p in products:
        images = p.images_json.get("items", []) if p.images_json else []
        specs = (p.raw_json or {}).get("specs", [])
        writer.writerow(
            [
                p.url,
                p.title or "",
                p.price_text or "",
                " | ".join(specs),
                images[0] if images else "",
                " | ".join(images),
            ]
        )

    output.seek(0)
    headers = {"Content-Disposition": "attachment; filename=motor3d_products.csv"}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)


@router.post("/run", response_model=Motor3DRunResponse)
async def run_all(payload: Motor3DRunRequest, db: AsyncSession = Depends(get_db)) -> Motor3DRunResponse:
    base = (payload.domain or "motor3dmodel.ir").replace("https://", "").replace("http://", "").strip("/")
    sitemap_url = f"https://{base}/wp-sitemap.xml"
    url_prefix = f"https://{base}/product/"

    project = await project_service.get(db, payload.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    policy = await domain_policy_service.get_by_domain(db, base)
    if not policy:
        policy = await domain_policy_service.create(
            db,
            domain=base,
            enabled=True,
            method="http",
            use_proxy=False,
            request_delay_ms=1000,
            max_concurrency=1,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            block_resources=True,
        )

    try:
        urls = await discover_product_urls(
            domain=base,
            sitemap_url=sitemap_url,
            url_prefix=url_prefix,
            policy=policy,
            max_urls=payload.max_urls,
        )
    except ValueError as ve:
        logger.exception("motor3d discover failed", extra={"domain": base})
        raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail=str(ve)[:200]) from ve
    except Exception as exc:  # noqa: BLE001
        logger.exception("motor3d run_all discover failed", extra={"domain": base})
        detail = "motor3d discover failed; see server logs"
        if settings.environment == "development":
            detail = f"{detail}: {str(exc)[:200]}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc

    created_jobs, rejected = await job_service.create_many_validated(
        db,
        project=project,
        urls=urls,
        topic_id=None,
        name_prefix="Motor3D product",
        skip_dedup=False,
    )

    for job in created_jobs:
        run_scrape_job.delay(job.id)

    return Motor3DRunResponse(
        count=len(urls),
        sample_urls=urls[:20],
        job_ids=[j.id for j in created_jobs],
        rejected=[{"url": u, "reason": r} for u, r in rejected],
    )
