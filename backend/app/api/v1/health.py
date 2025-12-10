from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__
from app.core.config import settings


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = settings.project_name
    version: str = __version__
    environment: str = settings.environment


router = APIRouter()


@router.get("/", response_model=HealthResponse, summary="Health check")
async def read_health() -> HealthResponse:
    """
    Lightweight health endpoint for probes.
    """
    return HealthResponse()
