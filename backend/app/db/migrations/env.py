"""
Alembic configuration for the project.

- Reads DATABASE_URL directly from the environment (no app settings import).
- Forces a synchronous driver for migrations (psycopg2) to keep Render pre-deploy stable.
"""

from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine.url import make_url

from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("DATABASE_URL is not set for Alembic migrations.")

    url = make_url(raw_url)

    # Prefer psycopg2 (sync) for migrations even if the runtime uses asyncpg.
    if url.drivername.startswith("postgresql+asyncpg"):
        url = url.set(drivername="postgresql+psycopg2")
    elif url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg2")

    return str(url)


def _configure_sqlalchemy_url() -> None:
    sync_url = _sync_database_url()
    config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    _configure_sqlalchemy_url()
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _configure_sqlalchemy_url()
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
