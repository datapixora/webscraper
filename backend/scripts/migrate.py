"""
Simple migration runner for Render predeploy or local automation.

Usage:
    python -m scripts.migrate
"""

from pathlib import Path
import sys

from alembic import command
from alembic.config import Config

from app.core.config import settings


def run_migrations() -> None:
    """
    Run Alembic migrations to head using the app's DATABASE_URL.
    Exits with a non-zero status on failure so Render marks the deploy as failed.
    """
    project_root = Path(__file__).resolve().parents[1]
    alembic_ini = project_root / "alembic.ini"

    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(project_root / "app" / "db" / "migrations"))
    cfg.set_main_option("sqlalchemy.url", settings.async_database_url)

    command.upgrade(cfg, "head")


if __name__ == "__main__":
    try:
        run_migrations()
    except Exception as exc:  # pragma: no cover - runtime guardrail
        print(f"[migrate] failed: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        print("[migrate] database is up to date")
