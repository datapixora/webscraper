from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal, TypedDict

import httpx
from bs4 import BeautifulSoup
from parsel import Selector
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urldefrag

from app.core.config import settings

ScrapeMethod = Literal["httpx", "playwright"]

logger = logging.getLogger(__name__)


class ExtractionField(TypedDict, total=False):
    name: str
    selector: str
    type: Literal["css", "xpath"]
    attr: str  # "text" or attribute name
    all: bool


class ScrapeResult(TypedDict):
    raw_html: str
    structured_data: dict[str, Any]
    method: ScrapeMethod


class PageCrawlResult(TypedDict):
    raw_html: str
    title: str | None
    text_content: str
    links: list[str]
    http_status: int | None


def _needs_js_render(html: str) -> bool:
    script_count = html.lower().count("<script")
    has_spa_markers = "__next" in html or "data-reactroot" in html or "ng-version" in html
    return script_count > 15 or has_spa_markers or len(html) < 5000


async def fetch_httpx(url: str, timeout: float | None = None) -> str:
    async with httpx.AsyncClient(
        timeout=timeout or settings.http_timeout, headers={"User-Agent": "WebScraperBot/1.0"}
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


async def fetch_httpx_response(url: str, timeout: float | None = None) -> httpx.Response:
    async with httpx.AsyncClient(
        timeout=timeout or settings.http_timeout,
        headers={"User-Agent": "WebScraperBot/1.0"},
        follow_redirects=True,
    ) as client:
        resp = await client.get(url)
        return resp


async def fetch_playwright(url: str, timeout: float | None = None) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=timeout or settings.playwright_timeout_ms,
        )
        # Give the page a moment to settle for dynamic content
        await page.wait_for_timeout(500)
        content = await page.content()
        await browser.close()
        return content


def extract_with_schema(html: str, extraction_schema: dict[str, Any] | None) -> dict[str, Any]:
    if not extraction_schema:
        return {}
    fields: list[ExtractionField] = extraction_schema.get("fields", [])
    sel = Selector(text=html)
    data: dict[str, Any] = {}

    for field in fields:
        name = field.get("name")
        selector = field.get("selector")
        if not name or not selector:
            continue
        sel_type = field.get("type", "css")
        attr = field.get("attr", "text")
        collect_all = field.get("all", False)

        def _extract(s: Selector) -> str:
            if attr == "text":
                return (s.get() or "").strip()
            return (s.attrib.get(attr) or "").strip()

        if sel_type == "xpath":
            nodes = sel.xpath(selector)
        else:
            nodes = sel.css(selector)

        if collect_all:
            data[name] = [_extract(n) for n in nodes]
        else:
            data[name] = _extract(nodes) if hasattr(nodes, "attrib") else _extract(nodes[0]) if nodes else ""

    return data


async def scrape_url(
    url: str, extraction_schema: dict[str, Any] | None = None, force_method: ScrapeMethod | None = None
) -> ScrapeResult:
    """
    Auto-detect static vs JS-heavy pages. Falls back to Playwright if needed.
    """
    raw_html = ""
    method_used: ScrapeMethod = "httpx"

    if force_method == "playwright":
        raw_html = await fetch_playwright(url)
        method_used = "playwright"
    else:
        try:
            raw_html = await fetch_httpx(url)
            if force_method == "httpx":
                method_used = "httpx"
            elif _needs_js_render(raw_html):
                try:
                    raw_html = await fetch_playwright(url)
                    method_used = "playwright"
                except Exception as playwright_err:  # noqa: BLE001
                    logger.warning("Playwright fallback failed; returning httpx content", exc_info=playwright_err)
                    method_used = "httpx"
        except Exception:
            # Fallback to Playwright on any static fetch failure
            raw_html = await fetch_playwright(url)
            method_used = "playwright"

    structured = extract_with_schema(raw_html, extraction_schema)
    return {"raw_html": raw_html, "structured_data": structured, "method": method_used}


def scrape_url_sync(
    url: str, extraction_schema: dict[str, Any] | None = None, force_method: ScrapeMethod | None = None
) -> ScrapeResult:
    return asyncio.run(scrape_url(url, extraction_schema, force_method))


def _extract_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()
    for tag in soup.find_all("a", href=True):
        href = tag.get("href", "").strip()
        if not href or href.startswith("javascript:") or href.startswith("mailto:"):
            continue
        abs_url = urljoin(base_url, href)
        abs_url = urldefrag(abs_url).url
        links.add(abs_url)
    return list(links)


def _extract_text_and_title(html: str) -> tuple[str | None, str]:
    soup = BeautifulSoup(html, "html.parser")
    # Remove script and style for cleaner text
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    text = soup.get_text(" ", strip=True)
    return title, text


async def crawl_page_for_campaign(url: str) -> PageCrawlResult:
    """
    Lightweight crawl for campaign: fetch, extract title/text, collect links.
    """
    try:
        resp = await fetch_httpx_response(url)
        raw_html = resp.text
        http_status = resp.status_code
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        response = exc.response
        return {
            "raw_html": response.text if response else "",
            "title": None,
            "text_content": "",
            "links": [],
            "http_status": response.status_code if response else None,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to crawl url", exc_info=exc, extra={"url": url})
        return {"raw_html": "", "title": None, "text_content": "", "links": [], "http_status": None}

    title, text_content = _extract_text_and_title(raw_html)
    links = _extract_links(str(resp.url), raw_html)
    return {
        "raw_html": raw_html,
        "title": title,
        "text_content": text_content,
        "links": links,
        "http_status": http_status,
    }
