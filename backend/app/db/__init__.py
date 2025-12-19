"""
Database package init kept minimal to avoid pulling application settings during Alembic runs.
"""

from app.db.base import Base  # noqa: F401

__all__ = ["Base"]
