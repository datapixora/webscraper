"""
Lightweight connectivity check for the database.

Usage:
    python -m scripts.db_ping
"""

import asyncio
import sys

from sqlalchemy import text

from app.db.session import AsyncSessionLocal


async def ping() -> bool:
    """
    Execute a trivial SELECT 1 to confirm the database is reachable.
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            print(f"[db_ping] result={value}")
            return bool(value)
    except Exception as exc:  # pragma: no cover - runtime guardrail
        print(f"[db_ping] failed: {exc}", file=sys.stderr)
        return False


if __name__ == "__main__":
    ok = asyncio.run(ping())
    sys.exit(0 if ok else 1)
