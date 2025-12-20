from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Literal, TypedDict

import httpx
import structlog
from bs4 import BeautifulSoup
from parsel import Selector
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urldefrag

from app.core.config import settings
from app.services.proxy_config import get_httpx_proxy_dict, get_playwright_proxy_dict

ScrapeMethod = Literal["httpx", "playwright"]

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


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
    http_status: int | None
    blocked: bool
    block_reason: str | None
    title: str | None


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


def _detect_block(
    *, status: int | None, title: str | None = None, html: str | None = None
) -> tuple[bool, str | None]:
    if status in {403, 429, 503}:
        return True, f"http_status_{status}"

    text = (title or "").lower()
    html_lower = (html or "").lower()
    title_markers = ["access denied", "forbidden", "attention required", "cloudflare"]
    html_markers = ["cf-chl", "captcha", "access denied", "forbidden", "cloudflare"]

    if any(marker in text for marker in title_markers):
        return True, "title_block_marker"
    if any(marker in html_lower for marker in html_markers):
        return True, "html_block_marker"

    return False, None


async def fetch_httpx(url: str, timeout: float | None = None) -> str:
    proxy_dict = get_httpx_proxy_dict()
    try:
        async with httpx.AsyncClient(
            timeout=timeout or settings.http_timeout,
            headers={"User-Agent": "WebScraperBot/1.0"},
            proxies=proxy_dict,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except httpx.ProxyError as e:
        structured_logger.error(
            "proxy_connection_failed",
            url=url,
            error=str(e),
            proxy_configured=proxy_dict is not None,
        )
        raise
    except httpx.HTTPStatusError as e:
        structured_logger.error("http_error", url=url, status=e.response.status_code)
        raise


async def fetch_httpx_response(url: str, timeout: float | None = None) -> httpx.Response:
    proxy_dict = get_httpx_proxy_dict()
    try:
        async with httpx.AsyncClient(
            timeout=timeout or settings.http_timeout,
            headers={"User-Agent": "WebScraperBot/1.0"},
            follow_redirects=True,
            proxies=proxy_dict,
        ) as client:
            resp = await client.get(url)
            return resp
    except httpx.ProxyError as e:
        structured_logger.error(
            "proxy_connection_failed",
            url=url,
            error=str(e),
            proxy_configured=proxy_dict is not None,
        )
        raise
    except httpx.HTTPStatusError as e:
        structured_logger.error("http_error", url=url, status=e.response.status_code)
        raise


async def fetch_playwright(url: str, timeout: float | None = None) -> str:
    proxy_config = get_playwright_proxy_dict()

    # Define blocked resource types and URL patterns for bandwidth optimization
    BLOCKED_RESOURCE_TYPES = ["image", "media", "font", "stylesheet"]
    BLOCKED_URL_PATTERNS = [
        r".*\.(jpg|jpeg|png|gif|webp|svg|ico)$",
        r".*\.(woff|woff2|ttf|eot)$",
        r".*\.(mp4|mp3|wav|webm)$",
        r".*(google-analytics|googletagmanager|facebook|doubleclick|analytics).*",
    ]

    async def route_handler(route):
        """Block unwanted resources to save bandwidth."""
        resource_type = route.request.resource_type
        url_to_check = route.request.url

        # Block unwanted resource types
        if resource_type in BLOCKED_RESOURCE_TYPES:
            await route.abort()
            return

        # Block unwanted URL patterns
        for pattern in BLOCKED_URL_PATTERNS:
            if re.match(pattern, url_to_check, re.IGNORECASE):
                await route.abort()
                return

        # Allow all other requests
        await route.continue_()

    try:
        async with async_playwright() as p:
            # Launch browser with proxy configuration
            browser = await p.chromium.launch(headless=True, proxy=proxy_config)
            context = await browser.new_context()
            page = await context.new_page()

            # Register route handler for resource blocking (if enabled)
            if settings.playwright_block_resources:
                await page.route("**/*", route_handler)

            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout or settings.playwright_timeout_ms,
            )
            # Give the page a moment to settle for dynamic content
            await page.wait_for_timeout(500)
            content = await page.content()
            await context.close()
            await browser.close()
            return content
    except Exception as e:
        # Catch Playwright errors including proxy errors
        error_msg = str(e)
        if "proxy" in error_msg.lower() or "net::" in error_msg.lower():
            structured_logger.error(
                "playwright_proxy_error",
                url=url,
                error=error_msg,
                proxy_configured=proxy_config is not None,
            )
        else:
            structured_logger.error("playwright_error", url=url, error=error_msg)
        raise


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
    http_status: int | None = None
    page_title: str | None = None
    blocked = False
    block_reason: str | None = None
    method_used: ScrapeMethod = "httpx"

    if force_method == "playwright":
        raw_html = await fetch_playwright(url)
        method_used = "playwright"
    else:
        try:
            resp = await fetch_httpx_response(url)
            raw_html = resp.text
            http_status = resp.status_code
            blocked, block_reason = _detect_block(status=http_status, html=raw_html)
            if blocked:
                method_used = "httpx"
                structured = extract_with_schema(raw_html, extraction_schema)
                return {
                    "raw_html": raw_html,
                    "structured_data": structured,
                    "method": method_used,
                    "http_status": http_status,
                    "blocked": blocked,
                    "block_reason": block_reason,
                    "title": None,
                }
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

    # If Playwright was used, capture block markers
    if method_used == "playwright":
        # Attempt to get title quickly via BeautifulSoup to avoid extra browser call
        soup = BeautifulSoup(raw_html, "html.parser")
        page_title = soup.title.string.strip() if soup.title and soup.title.string else None
        blocked, block_reason = _detect_block(status=http_status, title=page_title, html=raw_html)

    structured = extract_with_schema(raw_html, extraction_schema)
    return {
        "raw_html": raw_html,
        "structured_data": structured,
        "method": method_used,
        "http_status": http_status,
        "blocked": blocked,
        "block_reason": block_reason,
        "title": page_title,
    }


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
