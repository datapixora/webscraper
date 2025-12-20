"""
SmartProxy configuration service.

Provides helper functions to get proxy configuration for HTTP clients and browsers.
Supports both environment-based and database-based configuration.
"""
import os
import structlog
from typing import Dict, Optional
from urllib.parse import quote

from app.core.config import settings

logger = structlog.get_logger(__name__)


def _validate_proxy_config(config: Dict[str, any]) -> bool:
    """
    Validate that proxy configuration has all required fields.

    Args:
        config: Dictionary with proxy configuration

    Returns:
        bool: True if valid, False otherwise
    """
    required = ["host", "port", "username", "password"]
    for field in required:
        value = config.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            logger.warning("proxy_config_invalid", missing_field=field)
            return False
    return True


def _mask_credentials(username: str, password: str) -> Dict[str, str]:
    """Mask credentials for logging."""
    return {
        "username": "***" if username else None,
        "password": "***" if password else None,
    }


def is_enabled() -> bool:
    """
    Check if SmartProxy is enabled.

    PROXY_ENABLED env wins; if unset, fall back to settings.smartproxy_enabled.
    """
    env_val = os.getenv("PROXY_ENABLED")
    if env_val is not None:
        normalized = env_val.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False

    if not settings.smartproxy_enabled:
        return False

    config = {
        "host": settings.smartproxy_host,
        "port": settings.smartproxy_port,
        "username": settings.smartproxy_username,
        "password": settings.smartproxy_password,
    }

    return _validate_proxy_config(config)


def get_proxy_url(country: Optional[str] = None) -> Optional[str]:
    """
    Get formatted proxy URL for SmartProxy.

    Args:
        country: Optional country code (e.g., 'us', 'uk', 'de')

    Returns:
        str: Proxy URL in format http://username:password@host:port
        None: If proxy is disabled or invalid
    """
    if not settings.smartproxy_enabled:
        logger.debug("smartproxy_disabled", source="environment")
        return None

    host = settings.smartproxy_host
    port = settings.smartproxy_port
    username = settings.smartproxy_username
    password = settings.smartproxy_password
    country_code = country or settings.smartproxy_country

    config = {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
    }

    if not _validate_proxy_config(config):
        logger.warning("proxy_config_incomplete_proxy_disabled")
        return None

    # URL-encode credentials to handle special characters
    username_encoded = quote(username, safe="")
    password_encoded = quote(password, safe="")

    # SmartProxy country-specific format: user-country-code
    if country_code:
        username_encoded = f"{username_encoded}-country-{country_code}"

    proxy_url = f"http://{username_encoded}:{password_encoded}@{host}:{port}"

    # Log (with masked credentials)
    logger.info(
        "smartproxy_enabled",
        host=host,
        port=port,
        country=country_code,
        **_mask_credentials(username, password)
    )

    return proxy_url


def get_httpx_proxy_dict(country: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Get proxy configuration dict for httpx.AsyncClient.

    Args:
        country: Optional country code (e.g., 'us', 'uk', 'de')

    Returns:
        dict: {"http://": proxy_url, "https://": proxy_url}
        None: If proxy is disabled or invalid

    Example:
        proxies = get_httpx_proxy_dict()
        async with httpx.AsyncClient(proxies=proxies) as client:
            response = await client.get(url)
    """
    proxy_url = get_proxy_url(country)
    if not proxy_url:
        return None

    return {
        "http://": proxy_url,
        "https://": proxy_url,
    }


def get_playwright_proxy_dict(country: Optional[str] = None) -> Optional[Dict[str, any]]:
    """
    Get proxy configuration dict for Playwright browser launch.

    Args:
        country: Optional country code (e.g., 'us', 'uk', 'de')

    Returns:
        dict: {"server": url, "username": str, "password": str}
        None: If proxy is disabled or invalid

    Example:
        proxy_config = get_playwright_proxy_dict()
        browser = await p.chromium.launch(headless=True, proxy=proxy_config)
    """
    if not settings.smartproxy_enabled:
        return None

    host = settings.smartproxy_host
    port = settings.smartproxy_port
    username = settings.smartproxy_username
    password = settings.smartproxy_password
    country_code = country or settings.smartproxy_country

    config = {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
    }

    if not _validate_proxy_config(config):
        return None

    # SmartProxy country-specific format: user-country-code
    username_with_country = username
    if country_code:
        username_with_country = f"{username}-country-{country_code}"

    return {
        "server": f"http://{host}:{port}",
        "username": username_with_country,
        "password": password,
    }


# Future enhancement: Database-based configuration
# These functions will be enhanced in Phase 2 to check database first,
# then fall back to environment variables
async def get_proxy_url_from_db(country: Optional[str] = None) -> Optional[str]:
    """
    Get proxy URL from database settings (if available), fallback to environment.
    This function is a placeholder for Phase 2 implementation.
    """
    # TODO: Implement database lookup
    # from app.services.settings import SettingService
    # setting = await SettingService.get_by_key(db, "smartproxy")
    # if setting and setting.value:
    #     return build_proxy_url_from_db(setting.value, country)

    # Fallback to environment
    return get_proxy_url(country)
