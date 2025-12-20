import logging

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.api.router import api_router
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.proxy_config import is_enabled

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.project_name,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)
    return application


app = create_application()


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting WebScraper backend", extra={"environment": settings.environment})

    # Log proxy configuration status
    proxy_enabled = is_enabled()
    structured_logger.info(
        "application_startup",
        environment=settings.environment,
        smartproxy_enabled=proxy_enabled,
        smartproxy_host=settings.smartproxy_host if proxy_enabled else None,
        playwright_block_resources=settings.playwright_block_resources,
    )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Shutting down WebScraper backend")


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {"message": f"{settings.project_name} API", "version": __version__}


@app.get("/health", tags=["health"])
async def health() -> dict[str, str | bool]:
    """
    Render health probe: includes DB connectivity flag.
    """
    db_ok = True
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db_ok = False

    status = "ok" if db_ok else "degraded"
    return {"status": status, "db": db_ok}
