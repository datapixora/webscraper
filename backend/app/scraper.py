from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Literal, TypedDict, Optional, Dict
from urllib.parse import urlparse

import httpx
import structlog
from bs4 import BeautifulSoup
from parsel import Selector
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urldefrag
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.proxy_config import get_httpx_proxy_dict, get_playwright_proxy_dict
from app.services.domain_policy import domain_policy_service

ScrapeMethod = Literal["httpx", "playwright"]

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)

# Simple in-process semaphores to respect per-domain concurrency
_domain_semaphores: dict[str, asyncio.Semaphore] = {}


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


async def scrape_url_with_settings(
    url: str,
    db: AsyncSession,
    extraction_schema: dict[str, Any] | None = None,
    force_method: ScrapeMethod | None = None,
    job_id: Optional[str] = None,
) -> ScrapeResult:
    """
    Scrape URL with dynamic settings from database (proxy, delays, retries, etc).

    Args:
        url: Target URL
        db: Database session for fetching settings
        extraction_schema: Optional extraction schema
        force_method: Force specific scrape method (overrides policy)
        job_id: Job ID for sticky sessions

    Returns:
        ScrapeResult with raw HTML, structured data, and metadata
    """
    from app.services.proxy_manager import (
        get_proxy_settings,
        get_proxy_for_request,
        get_request_delay,
        should_retry_on_status,
        clear_sticky_session,
    )

    parsed = urlparse(url if "://" in url else f"https://{url}")
    domain = parsed.hostname or url

    domain_policy = await domain_policy_service.get_policy_for_url(db, domain)

    # Per-domain concurrency gate
    sem = _domain_semaphores.get(domain)
    if not sem:
        sem = asyncio.Semaphore(domain_policy.max_concurrency if domain_policy and domain_policy.enabled else 2)
        _domain_semaphores[domain] = sem

    proxy_settings = await get_proxy_settings(db)
    max_retries = proxy_settings.proxy_retry_count

    # Apply request delay (domain policy overrides)
    if domain_policy and domain_policy.enabled:
        delay_sec = max(domain_policy.request_delay_ms, 0) / 1000
    else:
        delay_sec = await get_request_delay(db)
    if delay_sec > 0:
        await asyncio.sleep(delay_sec)

    raw_html = ""
    http_status: int | None = None
    page_title: str | None = None
    blocked = False
    block_reason: str | None = None
    method_used: ScrapeMethod = "httpx"

    # Determine scrape method based on policy
    if force_method:
        target_method = force_method
    elif domain_policy and domain_policy.enabled:
        if domain_policy.method == "http":
            target_method = "httpx"
        elif domain_policy.method == "playwright":
            target_method = "playwright"
        else:
            target_method = None
    elif proxy_settings.scrape_method_policy == "http":
        target_method = "httpx"
    elif proxy_settings.scrape_method_policy == "browser":
        target_method = "playwright"
    else:  # auto
        target_method = None  # Will try httpx first, then playwright

    # Retry loop
    for attempt in range(max_retries + 1):
        is_retry = attempt > 0

        try:
            # Get proxy for this attempt (respect domain policy)
            httpx_proxy, playwright_proxy = await get_proxy_for_request(
                db, job_id=job_id, url=url, is_retry=is_retry
            )
            if domain_policy and domain_policy.enabled and not domain_policy.use_proxy:
                httpx_proxy = None
                playwright_proxy = None

            user_agent = domain_policy.user_agent if domain_policy and domain_policy.enabled else None
            block_resources = (
                domain_policy.block_resources if domain_policy and domain_policy.enabled else settings.playwright_block_resources
            )

            async with sem:
                if target_method == "playwright":
                    raw_html = await _fetch_playwright_with_proxy(
                        url, playwright_proxy, user_agent=user_agent, block_resources=block_resources
                    )
                    method_used = "playwright"
                    # Extract title and check for blocks
                    soup = BeautifulSoup(raw_html, "html.parser")
                    page_title = soup.title.string.strip() if soup.title and soup.title.string else None
                    blocked, block_reason = _detect_block(status=http_status, title=page_title, html=raw_html)
                    break  # Success
                else:
                    # Try httpx first (or if auto policy)
                    try:
                        resp = await _fetch_httpx_response_with_proxy(url, httpx_proxy, user_agent=user_agent)
                        raw_html = resp.text
                        http_status = resp.status_code
                        method_used = "httpx"

                        # Check for blocks
                        blocked, block_reason = _detect_block(status=http_status, html=raw_html)

                        if blocked:
                            # Check if we should retry
                            if is_retry or not await should_retry_on_status(db, http_status):
                                # Don't retry, return blocked result
                                break
                            else:
                                # Retry with new proxy
                                clear_sticky_session(job_id=job_id)
                                logger.warning(
                                    "blocked_retrying",
                                    url=url,
                                    status=http_status,
                                    reason=block_reason,
                                    attempt=attempt + 1,
                                )
                                continue

                        # Check if needs JS rendering (for auto policy)
                        if target_method is None and _needs_js_render(raw_html):
                            # Fallback to playwright
                            try:
                                raw_html = await _fetch_playwright_with_proxy(
                                    url, playwright_proxy, user_agent=user_agent, block_resources=block_resources
                                )
                                method_used = "playwright"
                                soup = BeautifulSoup(raw_html, "html.parser")
                                page_title = soup.title.string.strip() if soup.title and soup.title.string else None
                                blocked, block_reason = _detect_block(status=http_status, title=page_title, html=raw_html)
                            except Exception as playwright_err:
                                logger.warning("Playwright fallback failed", exc_info=playwright_err)
                                method_used = "httpx"

                        break  # Success

                    except httpx.HTTPStatusError as e:
                        http_status = e.response.status_code

                        # Check if we should retry
                        if await should_retry_on_status(db, http_status):
                            clear_sticky_session(job_id=job_id)
                            logger.warning(
                                "http_error_retrying",
                                url=url,
                                status=http_status,
                                attempt=attempt + 1,
                            )
                            continue
                        else:
                            # Don't retry, fall back to playwright if auto policy
                            if target_method is None:
                                raw_html = await _fetch_playwright_with_proxy(
                                    url, playwright_proxy, user_agent=user_agent, block_resources=block_resources
                                )
                                method_used = "playwright"
                                break
                            raise

        except Exception as exc:
            if attempt == max_retries:
                # Last attempt failed, raise
                logger.exception(f"Scrape failed all retries for {url}, attempts: {max_retries + 1}")
                raise
            else:
                # Retry
                clear_sticky_session(job_id=job_id)
                logger.warning(f"Scrape attempt failed, retrying: {url}, attempt: {attempt + 1}, error: {exc}")
                continue

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


async def _fetch_httpx_response_with_proxy(
    url: str, proxy_dict: Optional[Dict[str, str]], timeout: float | None = None, user_agent: Optional[str] = None
) -> httpx.Response:
    """Fetch URL with httpx using provided proxy configuration."""
    async with httpx.AsyncClient(
        timeout=timeout or settings.http_timeout,
        headers={"User-Agent": user_agent or "WebScraperBot/1.0"},
        follow_redirects=True,
        proxies=proxy_dict,
    ) as client:
        resp = await client.get(url)
        return resp


async def _fetch_playwright_with_proxy(
    url: str,
    proxy_config: Optional[Dict[str, any]],
    timeout: float | None = None,
    user_agent: Optional[str] = None,
    block_resources: bool = True,
    use_stealth: bool = True,
) -> str:
    """Fetch URL with Playwright using provided proxy configuration and anti-detection."""
    from urllib.parse import urlparse
    from app.services.stealth_browser import (
        apply_stealth_async,
        get_stealth_context_options,
        get_additional_browser_args,
        inject_stealth_scripts,
        load_session,
        save_session,
    )

    # Log proxy config for debugging
    if proxy_config:
        masked_config = {
            "server": proxy_config.get("server"),
            "username": "***" if proxy_config.get("username") else None,
            "password": "***" if proxy_config.get("password") else None,
        }
        structured_logger.debug("playwright_proxy_config", config=masked_config)

    BLOCKED_RESOURCE_TYPES = ["image", "media", "font", "stylesheet"]
    BLOCKED_URL_PATTERNS = [
        r".*\.(jpg|jpeg|png|gif|webp|svg|ico)$",
        r".*\.(woff|woff2|ttf|eot)$",
        r".*\.(mp4|mp3|wav|webm)$",
        r".*(google-analytics|googletagmanager|facebook|doubleclick|analytics).*",
    ]

    async def route_handler(route):
        resource_type = route.request.resource_type
        url_to_check = route.request.url

        if resource_type in BLOCKED_RESOURCE_TYPES:
            await route.abort()
            return

        for pattern in BLOCKED_URL_PATTERNS:
            if re.match(pattern, url_to_check, re.IGNORECASE):
                await route.abort()
                return

        await route.continue_()

    async with async_playwright() as p:
        # Launch browser with anti-detection args
        # Note: headless=False may help bypass some Cloudflare detection
        launch_options = {"headless": False, "proxy": proxy_config}
        if use_stealth:
            launch_options["args"] = get_additional_browser_args()
            # Override headless for stealth mode
            launch_options["headless"] = True  # Keep headless but with stealth modifications

        browser = await p.chromium.launch(**launch_options)

        # Create context with stealth options
        if use_stealth:
            context_options = get_stealth_context_options(user_agent=user_agent, randomize=True)
        else:
            context_options = {"user_agent": user_agent or "WebScraperBot/1.0"}

        context = await browser.new_context(**context_options)

        # Load previous session cookies if available (recommended by browserless.io)
        domain = urlparse(url).netloc
        if use_stealth and domain:
            await load_session(context, domain)

        page = await context.new_page()

        # Apply stealth modifications
        if use_stealth:
            await apply_stealth_async(page)
            await inject_stealth_scripts(page)

        if block_resources:
            await page.route("**/*", route_handler)

        # Navigate with longer wait for complex JS sites
        await page.goto(
            url,
            wait_until="networkidle",
            timeout=timeout or settings.playwright_timeout_ms,
        )

        # Wait for initial JavaScript to execute
        await page.wait_for_timeout(2000)

        # Check for CAPTCHA iframe (recommended by browserless.io)
        captcha_iframe = await page.query_selector('iframe[src*="captcha"]')
        if captcha_iframe:
            structured_logger.warning(
                "captcha_detected",
                has_iframe=True,
                message="CAPTCHA iframe found - requires solving service or manual intervention"
            )
            # Wait longer to see if auto-solving would help
            await page.wait_for_timeout(10000)

        # Check if we got a Cloudflare challenge
        page_text = await page.text_content("body") or ""
        if "cloudflare" in page_text.lower() or "just a moment" in page_text.lower():
            structured_logger.warning("cloudflare_challenge_detected", waiting=True)
            # Wait for Cloudflare JS challenge to resolve (typically 5-10 seconds)
            await page.wait_for_timeout(8000)

            # Check again if challenge resolved
            page_text_after = await page.text_content("body") or ""
            if "cloudflare" in page_text_after.lower():
                structured_logger.error(
                    "cloudflare_challenge_failed",
                    message="Challenge did not resolve after waiting"
                )

        content = await page.content()

        # Save session for future requests (if scrape was successful)
        # This makes subsequent requests look like a returning user
        if use_stealth and domain and content and len(content) > 1000:
            # Only save if we got substantial content (not just a block page)
            page_lower = content.lower()
            if not ("cloudflare" in page_lower or "access denied" in page_lower):
                await save_session(context, domain)

        await context.close()
        await browser.close()
        return content


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
