from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Iterable
from urllib.parse import urlparse

import httpx

from app.services.domain_policy import DomainPolicy, domain_policy_service
from app.services.proxy_config import get_httpx_proxy_dict

logger = logging.getLogger(__name__)


def _parse_locs(xml_text: str) -> list[str]:
    tree = ET.fromstring(xml_text)
    return [loc.text.strip() for loc in tree.iter("{*}loc") if loc.text]


async def _fetch_with_retry(client: httpx.AsyncClient, url: str, retries: int = 2) -> str:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning("motor3d_fetch_failed", url=url, attempt=attempt + 1, error=str(exc))
            await asyncio.sleep(0.5)
    raise last_exc  # type: ignore


def _is_product_sitemap(loc: str) -> bool:
    lowered = loc.lower()
    return any(key in lowered for key in ["product", "posts-product", "wc-product"])


def _is_product_url(loc: str, domain: str) -> bool:
    parsed = urlparse(loc)
    return parsed.hostname and domain in parsed.hostname and "/product/" in parsed.path


async def discover_product_urls(
    *,
    domain: str,
    sitemap_url: str,
    url_prefix: str,
    policy: DomainPolicy | None,
    max_urls: int = 2000,
) -> list[str]:
    # build client respecting policy
    headers = {
        "User-Agent": (policy.user_agent if policy and policy.user_agent else "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    }
    proxies = get_httpx_proxy_dict() if policy and policy.use_proxy and policy.enabled else None
    async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True, proxies=proxies) as client:
        seen: set[str] = set()
        to_visit = [sitemap_url]
        delay = max((policy.request_delay_ms if policy and policy.enabled else 0), 0) / 1000

        while to_visit and len(seen) < max_urls:
            current = to_visit.pop()
            xml_text = await _fetch_with_retry(client, current)
            locs = _parse_locs(xml_text)

            # sitemapindex or urlset
            product_sitemaps: list[str] = []
            product_urls: list[str] = []
            for loc in locs:
                if loc.endswith(".xml"):
                    if _is_product_sitemap(loc):
                        product_sitemaps.append(loc)
                    else:
                        # still may contain product URLs; include to crawl
                        product_sitemaps.append(loc)
                elif _is_product_url(loc, domain):
                    product_urls.append(loc)

            for loc in product_urls:
                if len(seen) >= max_urls:
                    break
                if loc.startswith(url_prefix) or _is_product_url(loc, domain):
                    seen.add(loc)

            for sm in product_sitemaps:
                to_visit.append(sm)

            if delay > 0 and to_visit:
                await asyncio.sleep(delay)

        return sorted(seen)
