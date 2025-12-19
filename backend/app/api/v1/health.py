from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.core.config import settings
from app.db.session import AsyncSessionLocal


class HealthResponse(BaseModel):
    status: str
    service: str = settings.project_name
    version: str = __version__
    environment: str = settings.environment
    db: bool


router = APIRouter()


async def check_db() -> bool:
    """
    Execute a simple query to confirm DB connectivity.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


@router.get("/", response_model=HealthResponse, summary="Health check")
async def read_health() -> HealthResponse:
    """
    Lightweight health endpoint for probes, including DB reachability.
    """
    db_ok = await check_db()

    status = "ok" if db_ok else "degraded"
    return HealthResponse(status=status, db=db_ok)
