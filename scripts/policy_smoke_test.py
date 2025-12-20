import asyncio

from app.db.session import AsyncSessionLocal
from app.services.domain_policy import domain_policy_service


async def main() -> None:
    url = "https://example.com/page"
    async with AsyncSessionLocal() as db:
        policy = await domain_policy_service.get_policy_for_url(db, url)
        print("Policy:", policy.domain if policy else "none")


if __name__ == "__main__":
    asyncio.run(main())
