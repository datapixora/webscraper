"""
Dynamic proxy configuration manager with database-backed settings and caching.

Handles:
- Database-backed proxy settings with 60s cache
- Sticky sessions with configurable TTL
- Rotation strategies (per_job, on_failure, per_request)
- Retry logic and request delays
"""
import asyncio
import hashlib
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import random

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.schemas.proxy_settings import ProxySettings
from app.services.settings import setting_service

logger = structlog.get_logger(__name__)

# Cache for proxy settings (60s TTL)
_settings_cache: Optional[Tuple[ProxySettings, float]] = None
_CACHE_TTL_SEC = 60

# Sticky session storage: {session_id: (proxy_url, expiry_time)}
_sticky_sessions: Dict[str, Tuple[str, float]] = {}


def _get_session_id(job_id: Optional[str] = None, url: Optional[str] = None) -> str:
    """Generate a session ID for sticky sessions."""
    if job_id:
        return f"job_{job_id}"
    if url:
        # Use URL hash for consistent session per domain
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"url_{url_hash}"
    return "default"


def _cleanup_expired_sessions():
    """Remove expired sticky sessions."""
    now = time.time()
    expired_keys = [key for key, (_, expiry) in _sticky_sessions.items() if expiry < now]
    for key in expired_keys:
        del _sticky_sessions[key]


async def get_proxy_settings(db: AsyncSession) -> ProxySettings:
    """
    Get proxy settings from database with 60s caching.

    Args:
        db: Database session

    Returns:
        ProxySettings object
    """
    global _settings_cache

    now = time.time()

    # Check cache
    if _settings_cache is not None:
        settings_obj, cache_time = _settings_cache
        if now - cache_time < _CACHE_TTL_SEC:
            return settings_obj

    # Fetch from database
    setting = await setting_service.get_by_key(db, "proxy_config")

    if setting and setting.value:
        proxy_settings = ProxySettings(**setting.value)
    else:
        # Return defaults if not configured
        proxy_settings = ProxySettings()

    # Update cache
    _settings_cache = (proxy_settings, now)

    logger.info("proxy_settings_loaded", enabled=proxy_settings.proxy_enabled, provider=proxy_settings.proxy_provider)

    return proxy_settings


def _build_proxy_url(
    proxy_settings: ProxySettings, session_id: Optional[str] = None, force_new: bool = False
) -> Optional[str]:
    """
    Build proxy URL based on settings.

    Args:
        proxy_settings: Proxy configuration
        session_id: Session ID for sticky sessions
        force_new: Force new proxy (ignore sticky session)

    Returns:
        Proxy URL or None if proxy disabled
    """
    if not proxy_settings.proxy_enabled:
        return None

    # Check if we should use environment credentials (fallback)
    host = app_settings.smartproxy_host
    port = app_settings.smartproxy_port
    username = app_settings.smartproxy_username
    password = app_settings.smartproxy_password

    if not all([host, port, username, password]):
        logger.warning("proxy_credentials_missing", provider=proxy_settings.proxy_provider)
        return None

    # Handle sticky sessions
    if proxy_settings.proxy_sticky_enabled and session_id and not force_new:
        _cleanup_expired_sessions()

        if session_id in _sticky_sessions:
            proxy_url, expiry = _sticky_sessions[session_id]
            if expiry > time.time():
                logger.debug("using_sticky_session", session_id=session_id)
                return proxy_url

    # Build new proxy URL with country targeting
    from urllib.parse import quote

    username_encoded = quote(username, safe="")
    password_encoded = quote(password, safe="")

    # Add country suffix if specified
    if proxy_settings.proxy_country:
        username_encoded = f"{username_encoded}-country-{proxy_settings.proxy_country}"

    proxy_url = f"http://{username_encoded}:{password_encoded}@{host}:{port}"

    # Store in sticky session if enabled
    if proxy_settings.proxy_sticky_enabled and session_id:
        expiry = time.time() + proxy_settings.proxy_sticky_ttl_sec
        _sticky_sessions[session_id] = (proxy_url, expiry)
        logger.debug(
            "created_sticky_session",
            session_id=session_id,
            ttl_sec=proxy_settings.proxy_sticky_ttl_sec,
        )

    return proxy_url


async def get_proxy_for_request(
    db: AsyncSession,
    job_id: Optional[str] = None,
    url: Optional[str] = None,
    is_retry: bool = False,
) -> Tuple[Optional[Dict[str, str]], Optional[Dict[str, any]]]:
    """
    Get proxy configuration for a request based on rotation strategy.

    Args:
        db: Database session
        job_id: Job ID (for per_job rotation)
        url: Target URL (for per_request rotation)
        is_retry: Whether this is a retry attempt (forces new proxy for on_failure strategy)

    Returns:
        Tuple of (httpx_proxy_dict, playwright_proxy_dict)
    """
    proxy_settings = await get_proxy_settings(db)

    if not proxy_settings.proxy_enabled:
        return None, None

    # Determine session ID based on rotation strategy
    session_id = None
    force_new = False

    if proxy_settings.proxy_rotation_strategy == "per_job":
        session_id = _get_session_id(job_id=job_id)
    elif proxy_settings.proxy_rotation_strategy == "on_failure":
        session_id = _get_session_id(job_id=job_id)
        force_new = is_retry  # Force new proxy on retry
    elif proxy_settings.proxy_rotation_strategy == "per_request":
        # No session - always use new proxy
        force_new = True

    proxy_url = _build_proxy_url(proxy_settings, session_id, force_new)

    if not proxy_url:
        return None, None

    # Build httpx proxy dict
    httpx_proxy = {
        "http://": proxy_url,
        "https://": proxy_url,
    }

    # Build playwright proxy dict
    # Extract components from proxy_url
    import re

    match = re.match(r"http://([^:]+):([^@]+)@([^:]+):(\d+)", proxy_url)
    if match:
        username, password, host, port = match.groups()
        from urllib.parse import unquote

        playwright_proxy = {
            "server": f"http://{host}:{port}",
            "username": unquote(username),
            "password": unquote(password),
        }
    else:
        playwright_proxy = None

    return httpx_proxy, playwright_proxy


async def get_request_delay(db: AsyncSession) -> float:
    """
    Get random delay between requests based on settings.

    Args:
        db: Database session

    Returns:
        Delay in seconds (float)
    """
    proxy_settings = await get_proxy_settings(db)

    if proxy_settings.request_delay_min_ms == 0 and proxy_settings.request_delay_max_ms == 0:
        return 0.0

    delay_ms = random.uniform(proxy_settings.request_delay_min_ms, proxy_settings.request_delay_max_ms)
    return delay_ms / 1000.0


def clear_sticky_session(job_id: Optional[str] = None, url: Optional[str] = None):
    """
    Clear a sticky session (e.g., after block detection).

    Args:
        job_id: Job ID
        url: Target URL
    """
    session_id = _get_session_id(job_id=job_id, url=url)
    if session_id in _sticky_sessions:
        del _sticky_sessions[session_id]
        logger.info("sticky_session_cleared", session_id=session_id)


async def should_retry_on_status(db: AsyncSession, status_code: int) -> bool:
    """
    Check if we should retry based on HTTP status code and settings.

    Args:
        db: Database session
        status_code: HTTP status code

    Returns:
        True if should retry
    """
    # Always retry on common block statuses
    return status_code in {403, 429, 503}
