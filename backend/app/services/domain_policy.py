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

    async def create(self, db: AsyncSession, *, domain: str, enabled: bool = True, config: Optional[dict[str, Any]] = None) -> DomainPolicy:
        policy = DomainPolicy(domain=self.normalize_domain(domain), enabled=enabled, config=config or {})
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
        config: Optional[dict[str, Any]] = None,
    ) -> DomainPolicy:
        if enabled is not None:
            policy.enabled = enabled
        if config is not None:
            policy.config = config
        await db.commit()
        await db.refresh(policy)
        return policy

    async def get_policy_for_url(self, db: AsyncSession, url: str) -> Optional[DomainPolicy]:
        domain = self.normalize_domain(url)
        return await self.get_by_domain(db, domain)


domain_policy_service = DomainPolicyService()

__all__ = ["domain_policy_service", "DomainPolicyService"]
