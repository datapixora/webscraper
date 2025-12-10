"""
SQLAlchemy declarative base and model registry.
Import models here so Alembic can auto-detect metadata.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models to register them with Base.metadata
from app.models.project import Project  # noqa: E402
from app.models.job import Job  # noqa: E402
from app.models.result import Result  # noqa: E402
from app.models.topic_campaign import TopicCampaign  # noqa: E402
from app.models.crawled_page import CrawledPage  # noqa: E402
from app.models.topic import Topic  # noqa: E402
from app.models.topic_url import TopicURL  # noqa: E402

__all__ = ["Base", "Project", "Job", "Result", "TopicCampaign", "CrawledPage", "Topic", "TopicURL"]
