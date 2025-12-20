import asyncio
import httpx
import pytest

from app.api.v1 import admin_motor3d


def test_parse_sitemap_basic():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://motor3dmodel.ir/product/a</loc></url>
      <url><loc>https://motor3dmodel.ir/product/b</loc></url>
    </urlset>
    """
    locs = admin_motor3d._parse_sitemap(xml)
    assert "https://motor3dmodel.ir/product/a" in locs
    assert "https://motor3dmodel.ir/product/b" in locs


@pytest.mark.anyio
async def test_discover_uses_sitemap(monkeypatch):
    # Prepare XML for root and child sitemap
    root_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://motor3dmodel.ir/product-sitemap.xml</loc></sitemap>
    </sitemapindex>
    """
    child_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://motor3dmodel.ir/product/widget-1</loc></url>
      <url><loc>https://motor3dmodel.ir/product/widget-2</loc></url>
    </urlset>
    """

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("wp-sitemap.xml"):
            return httpx.Response(200, text=root_xml)
        if request.url.path.endswith("product-sitemap.xml"):
            return httpx.Response(200, text=child_xml)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def fake_make_client(use_proxy: bool, user_agent: str | None):
        return httpx.AsyncClient(transport=transport)

    async def fake_get_policy(db, domain):
        return None

    monkeypatch.setattr(admin_motor3d, "_make_client", fake_make_client)
    monkeypatch.setattr(admin_motor3d.domain_policy_service, "get_by_domain", fake_get_policy)

    payload = admin_motor3d.Motor3DDiscoverRequest()
    resp = await admin_motor3d.discover_products(payload, db=None)  # db unused due to monkeypatch
    assert resp.count == 2
    assert len(resp.urls) == 2
    assert resp.sample_urls[0].startswith("https://motor3dmodel.ir/product/")
