from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Iterable
from urllib.parse import urlparse

import httpx

from app.services.domain_policy import DomainPolicy
from app.services.proxy_config import get_httpx_proxy_dict

logger = logging.getLogger(__name__)


def _parse_locs(xml_text: str) -> list[str]:
    tree = ET.fromstring(xml_text)
    return [loc.text.strip() for loc in tree.iter("{*}loc") if loc.text]


async def _fetch_with_retry(client: httpx.AsyncClient, url: str, retries: int = 2) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            url_str = str(url)
            resp = await client.get(url_str)
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning(
                "motor3d_fetch_failed url=%s attempt=%s error=%s",
                str(url),
                attempt + 1,
                str(exc),
            )
            await asyncio.sleep(0.5)
    raise last_exc  # type: ignore


def _is_product_sitemap(loc: str) -> bool:
    lowered = loc.lower()
    return any(key in lowered for key in ["posts-product", "product", "wc-product"])


def _is_product_url(loc: str, domain: str) -> bool:
    parsed = urlparse(loc)
    return parsed.hostname and domain in parsed.hostname and "/product/" in parsed.path


async def _build_client(use_proxy: bool, user_agent: str | None) -> httpx.AsyncClient:
    headers = {
        "User-Agent": user_agent
        or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    proxies = get_httpx_proxy_dict() if use_proxy else None
    return httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True, proxies=proxies)


def _ensure_xml_response(resp: httpx.Response) -> str:
    ctype = resp.headers.get("content-type", "").lower()
    text = resp.text
    if "xml" not in ctype or text.lstrip().lower().startswith("<!doctype html") or text.lstrip().lower().startswith(
        "<html"
    ):
        preview = text[:200]
        raise ValueError(f"Expected XML sitemap but got non-XML response: {preview}")
    return text


async def _discover_with_client(
    *,
    client: httpx.AsyncClient,
    domain: str,
    sitemap_url: str,
    url_prefix: str,
    delay: float,
    max_urls: int,
) -> list[str]:
    seen: set[str] = set()
    to_visit = [sitemap_url]
    product_sitemaps_seen: set[str] = set()

    while to_visit and len(seen) < max_urls:
        current = str(to_visit.pop())
        resp = await _fetch_with_retry(client, current)
        xml_text = _ensure_xml_response(resp)
        locs = _parse_locs(xml_text)

        product_sitemaps: list[str] = []
        product_urls: list[str] = []
        for loc in locs:
            if loc.endswith(".xml"):
                if _is_product_sitemap(loc):
                    product_sitemaps.append(loc)
            elif _is_product_url(loc, domain):
                product_urls.append(loc)

        for loc in product_urls:
            if len(seen) >= max_urls:
                break
            if loc.startswith(url_prefix) or _is_product_url(loc, domain):
                seen.add(loc)

        for sm in product_sitemaps:
            if sm not in product_sitemaps_seen:
                product_sitemaps_seen.add(sm)
                to_visit.append(sm)

        if delay > 0 and to_visit:
            await asyncio.sleep(delay)

    logger.info(
        "motor3d_discover_finished",
        domain=domain,
        sitemap_url=sitemap_url,
        product_sitemaps=len(product_sitemaps_seen),
        urls=len(seen),
        max_urls=max_urls,
    )
    return sorted(seen)


async def discover_product_urls(
    *,
    domain: str,
    sitemap_url: str,
    url_prefix: str,
    policy: DomainPolicy | None,
    max_urls: int = 2000,
) -> list[str]:
    delay = max((policy.request_delay_ms if policy and policy.enabled else 0), 0) / 1000
    ua = policy.user_agent if policy and policy.enabled else None
    use_proxy_flag = bool(policy and policy.enabled and policy.use_proxy)

    errors: list[str] = []
    # Try without proxy first, then with proxy if allowed
    for proxy_mode in [False, True] if use_proxy_flag else [False]:
        client = await _build_client(proxy_mode, ua)
        try:
            return await _discover_with_client(
                client=client,
                domain=domain,
                sitemap_url=sitemap_url,
                url_prefix=url_prefix,
                delay=delay,
                max_urls=max_urls,
            )
        except ValueError as ve:
            errors.append(str(ve))
            logger.warning(
                "motor3d_discover_non_xml use_proxy=%s error=%s", proxy_mode, str(ve)
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
            logger.warning(
                "motor3d_discover_failed_attempt use_proxy=%s error=%s",
                proxy_mode,
                str(exc),
            )
        finally:
            await client.aclose()

    # If all attempts failed
    raise RuntimeError("; ".join(errors))
