from __future__ import annotations

from typing import Any, Optional
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_policy import DomainPolicy


class DomainPolicyService:
    @staticmethod
    def normalize_domain(value: str) -> str:
        """
        Accepts URL or bare domain and returns lowercase host without scheme/port/path.
        """
        candidate = value.strip().lower()
        parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
        return parsed.hostname or candidate

    async def list(self, db: AsyncSession) -> list[DomainPolicy]:
        rows = await db.execute(select(DomainPolicy).order_by(DomainPolicy.domain))
        return list(rows.scalars().all())

    async def get(self, db: AsyncSession, policy_id: str) -> Optional[DomainPolicy]:
        return await db.get(DomainPolicy, policy_id)

    async def get_by_domain(self, db: AsyncSession, domain: str) -> Optional[DomainPolicy]:
        norm = self.normalize_domain(domain)
        rows = await db.execute(select(DomainPolicy).where(DomainPolicy.domain == norm))
        return rows.scalars().first()

    async def create(
        self,
        db: AsyncSession,
        *,
        domain: str,
        enabled: bool = True,
        method: str = "auto",
        use_proxy: bool = False,
        request_delay_ms: int = 1000,
        max_concurrency: int = 2,
        user_agent: Optional[str] = None,
        block_resources: bool = True,
    ) -> DomainPolicy:
        policy = DomainPolicy(
            domain=self.normalize_domain(domain),
            enabled=enabled,
            method=method,
            use_proxy=use_proxy,
            request_delay_ms=request_delay_ms,
            max_concurrency=max_concurrency,
            user_agent=user_agent,
            block_resources=block_resources,
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    async def update(
        self,
        db: AsyncSession,
        policy: DomainPolicy,
        *,
        enabled: Optional[bool] = None,
        method: Optional[str] = None,
        use_proxy: Optional[bool] = None,
        request_delay_ms: Optional[int] = None,
        max_concurrency: Optional[int] = None,
        user_agent: Optional[str] = None,
        block_resources: Optional[bool] = None,
    ) -> DomainPolicy:
        if enabled is not None:
            policy.enabled = enabled
        if method is not None:
            policy.method = method
        if use_proxy is not None:
            policy.use_proxy = use_proxy
        if request_delay_ms is not None:
            policy.request_delay_ms = request_delay_ms
        if max_concurrency is not None:
            policy.max_concurrency = max_concurrency
        if user_agent is not None:
            policy.user_agent = user_agent
        if block_resources is not None:
            policy.block_resources = block_resources
        await db.commit()
        await db.refresh(policy)
        return policy

    async def get_policy_for_url(self, db: AsyncSession, url: str) -> Optional[DomainPolicy]:
        domain = self.normalize_domain(url)
        return await self.get_by_domain(db, domain)


domain_policy_service = DomainPolicyService()

__all__ = ["domain_policy_service", "DomainPolicyService"]
