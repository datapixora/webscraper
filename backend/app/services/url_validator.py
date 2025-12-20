"""
Lightweight URL validation and quota enforcement helpers.

This stub keeps Render startup unblocked by providing the interface used in
job creation. It currently allows all URLs and does not enforce quotas; extend
with real logic as needed.
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


@dataclass
class UrlValidationResult:
    allowed: bool
    reason: Optional[str] = None


class UrlValidator:
    async def validate_url(
        self, db: AsyncSession, project: Project, url: str, skip_dedup: bool = False
    ) -> UrlValidationResult:
        # TODO: implement dedup checks and include/exclude pattern enforcement
        return UrlValidationResult(allowed=True, reason=None)

    async def enforce_quota(
        self, db: AsyncSession, project: Project, urls: list[str]
    ) -> tuple[list[str], list[tuple[str, str]]]:
        """
        Optionally enforce per-run / total quotas. Currently passthrough.
        Returns (accepted_urls, rejected[(url, reason)]).
        """
        cleaned = [u for u in urls if u]
        return cleaned, []


url_validator = UrlValidator()

__all__ = ["UrlValidationResult", "UrlValidator", "url_validator"]
