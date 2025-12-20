import asyncio

from app.connectors.motor3d import discover_product_urls
from app.services.domain_policy import DomainPolicy


async def main():
    policy = DomainPolicy(
        domain="motor3dmodel.ir",
        enabled=True,
        method="http",
        use_proxy=False,
        request_delay_ms=500,
        max_concurrency=1,
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        block_resources=True,
    )
    urls = await discover_product_urls(
        domain="motor3dmodel.ir",
        sitemap_url="https://motor3dmodel.ir/wp-sitemap.xml",
        url_prefix="https://motor3dmodel.ir/product/",
        policy=policy,
        max_urls=50,
    )
    print(f"Found {len(urls)} urls")
    for u in urls[:5]:
        print(u)


if __name__ == "__main__":
    asyncio.run(main())
