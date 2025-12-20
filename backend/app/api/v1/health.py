from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.core.config import settings
from app.db.session import get_db


class HealthResponse(BaseModel):
    status: str = "ok"
    db: bool = False
    service: str = settings.project_name
    version: str = __version__
    environment: str = settings.environment


router = APIRouter()


@router.get("/", response_model=HealthResponse, summary="Health check")
async def read_health(session: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health endpoint that validates DB connectivity.
    """
    status = "ok"
    db_ok = True

    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        status = "degraded"
        db_ok = False

    return HealthResponse(status=status, db=db_ok)
