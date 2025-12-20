from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.projects import router as projects_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.topics import router as topics_router
from app.api.v1.exports import router as exports_router
from app.api.v1.settings import router as settings_router
from app.api.v1.admin_settings import router as admin_settings_router

api_router = APIRouter()

# Versioned API
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router, prefix="/health", tags=["health"])
v1_router.include_router(projects_router, prefix="/projects", tags=["projects"])
v1_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
v1_router.include_router(campaigns_router, prefix="/campaigns", tags=["campaigns"])
v1_router.include_router(topics_router, prefix="/topics", tags=["topics"])
v1_router.include_router(exports_router, prefix="/exports", tags=["exports"])
v1_router.include_router(settings_router, prefix="/settings", tags=["settings"])
v1_router.include_router(admin_settings_router, prefix="/admin/settings", tags=["admin"])

api_router.include_router(v1_router, prefix="/api")

__all__ = ["api_router"]
