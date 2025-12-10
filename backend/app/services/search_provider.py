from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Protocol
from urllib.parse import parse_qs, urlparse, unquote

import httpx
from bs4 import BeautifulSoup


@dataclass
class SearchResult:
    url: str
    title: str | None
    snippet: str | None
    rank: int


class SearchProvider(Protocol):
    async def search_web(self, query: str, max_results: int) -> List[SearchResult]: ...


class MockSearchProvider:
    async def search_web(self, query: str, max_results: int) -> List[SearchResult]:
        base = [
            SearchResult(url="https://example.com", title="Example Domain", snippet="Example snippet", rank=1),
            SearchResult(
                url="https://www.wikipedia.org/",
                title="Wikipedia",
                snippet="The free encyclopedia",
                rank=2,
            ),
            SearchResult(
                url="https://news.ycombinator.com/",
                title="Hacker News",
                snippet="Tech news",
                rank=3,
            ),
        ]
        return base[:max_results]


class DuckDuckGoSearchProvider:
    async def search_web(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Lightweight HTML scrape of DuckDuckGo results. No API key required.
        """
        url = "https://duckduckgo.com/html/"
        params = {"q": query}
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True, timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            results: List[SearchResult] = []
            for rank, res in enumerate(soup.select(".result"), start=1):
                if len(results) >= max_results:
                    break
                link = res.select_one(".result__a")
                snippet_el = res.select_one(".result__snippet")
                if not link:
                    continue
                href = link.get("href", "").strip()
                # DuckDuckGo wraps targets as /l/?kh=-1&uddg=<url>
                parsed = urlparse(href)
                if "uddg" in parse_qs(parsed.query):
                    href = unquote(parse_qs(parsed.query).get("uddg", [""])[0])
                title = link.get_text(strip=True) or None
                snippet = snippet_el.get_text(" ", strip=True) if snippet_el else None
                if href:
                    results.append(SearchResult(url=href, title=title, snippet=snippet, rank=rank))
            return results


def get_search_provider() -> SearchProvider:
    provider_name = os.getenv("SEARCH_PROVIDER", "duckduckgo").lower()
    if provider_name == "mock":
        return MockSearchProvider()
    # Default to DuckDuckGo HTML scraping
    return DuckDuckGoSearchProvider()


search_provider = get_search_provider()

__all__ = ["search_provider", "SearchResult"]
