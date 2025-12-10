from celery import Celery

from app.core.config import settings

celery_app = Celery("webscraper")
celery_app.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.celery_task_time_limit,
)

# Discover tasks in this package.
celery_app.autodiscover_tasks(packages=["app.workers"])

# Celery looks for an `app` attribute by default when using `-A`.
app = celery_app

__all__ = ["celery_app", "app"]
