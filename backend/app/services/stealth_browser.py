"""
Anti-detection and stealth features for web scraping.

Provides:
- Playwright stealth plugin integration
- Browser fingerprint randomization
- User agent rotation
- Viewport randomization
- Timezone and locale spoofing
- Session persistence with cookies
"""
import json
import random
from pathlib import Path
from typing import Optional, Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)

# Session storage directory
SESSION_DIR = Path("/tmp/playwright_sessions")
SESSION_DIR.mkdir(exist_ok=True)


class StealthConfig:
    """Configuration for stealth browser settings."""

    # Common screen resolutions
    SCREEN_RESOLUTIONS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
        {"width": 1280, "height": 720},
    ]

    # Common user agents (Chrome on Windows)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]

    # Timezones
    TIMEZONES = [
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Phoenix",
    ]

    # Locales
    LOCALES = ["en-US", "en-GB", "en-CA"]

    @staticmethod
    def get_random_viewport() -> Dict[str, int]:
        """Get random viewport dimensions."""
        resolution = random.choice(StealthConfig.SCREEN_RESOLUTIONS)
        return resolution

    @staticmethod
    def get_random_user_agent() -> str:
        """Get random user agent."""
        return random.choice(StealthConfig.USER_AGENTS)

    @staticmethod
    def get_random_timezone() -> str:
        """Get random timezone."""
        return random.choice(StealthConfig.TIMEZONES)

    @staticmethod
    def get_random_locale() -> str:
        """Get random locale."""
        return random.choice(StealthConfig.LOCALES)


async def apply_stealth_async(page):
    """
    Apply stealth modifications to a Playwright page.

    This function uses playwright-stealth to hide automation indicators.
    Must be called after page creation.

    Args:
        page: Playwright page object
    """
    try:
        from playwright_stealth import stealth_async
        await stealth_async(page)
        logger.debug("stealth_applied", success=True)
    except ImportError:
        logger.warning("playwright_stealth_not_installed")
    except Exception as e:
        logger.error("stealth_application_failed", error=str(e))


def get_stealth_context_options(
    user_agent: Optional[str] = None,
    randomize: bool = True,
) -> Dict[str, Any]:
    """
    Get browser context options with anti-detection features.

    Args:
        user_agent: Custom user agent (if None, uses random)
        randomize: Whether to randomize fingerprint

    Returns:
        Dictionary of context options for browser.new_context()
    """
    viewport = StealthConfig.get_random_viewport() if randomize else StealthConfig.SCREEN_RESOLUTIONS[0]
    ua = user_agent or (StealthConfig.get_random_user_agent() if randomize else StealthConfig.USER_AGENTS[0])
    timezone = StealthConfig.get_random_timezone() if randomize else StealthConfig.TIMEZONES[0]
    locale = StealthConfig.get_random_locale() if randomize else StealthConfig.LOCALES[0]

    context_options = {
        "viewport": viewport,
        "user_agent": ua,
        "locale": locale,
        "timezone_id": timezone,
        "geolocation": {"latitude": 37.7749, "longitude": -122.4194},  # San Francisco
        "permissions": ["geolocation"],
        "color_scheme": "light",
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
        "java_script_enabled": True,
        "bypass_csp": True,
        "ignore_https_errors": True,
    }

    logger.debug(
        "stealth_context_created",
        viewport=viewport,
        timezone=timezone,
        locale=locale,
        ua_length=len(ua),
    )

    return context_options


def get_additional_browser_args() -> List[str]:
    """
    Get additional Chromium arguments for anti-detection.

    Returns:
        List of command-line arguments
    """
    return [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-accelerated-2d-canvas",
        "--no-first-run",
        "--no-zygote",
        "--disable-gpu",
        "--window-size=1920,1080",
    ]


async def inject_stealth_scripts(page):
    """
    Inject additional JavaScript to hide automation.

    Args:
        page: Playwright page object
    """
    stealth_js = """
    // Overwrite the `plugins` property to use a custom getter.
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });

    // Overwrite the `languages` property to use a custom getter.
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });

    // Overwrite the `webdriver` property to use a custom getter.
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
    });

    // Mock chrome object
    window.chrome = {
        runtime: {},
    };

    // Mock permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    """

    try:
        await page.add_init_script(stealth_js)
        logger.debug("stealth_scripts_injected")
    except Exception as e:
        logger.error("stealth_script_injection_failed", error=str(e))


def get_session_file(domain: str) -> Path:
    """
    Get session file path for a domain.

    Args:
        domain: Domain name (e.g., 'bidfax.info')

    Returns:
        Path to session file
    """
    safe_domain = domain.replace(".", "_").replace(":", "_")
    return SESSION_DIR / f"{safe_domain}_session.json"


async def save_session(context, domain: str):
    """
    Save browser session (cookies, localStorage) for a domain.

    Args:
        context: Playwright browser context
        domain: Domain name to save session for
    """
    try:
        session_file = get_session_file(domain)
        cookies = await context.cookies()

        session_data = {
            "cookies": cookies,
            "domain": domain,
        }

        with open(session_file, "w") as f:
            json.dump(session_data, f)

        logger.info("session_saved", domain=domain, cookie_count=len(cookies))
    except Exception as e:
        logger.error("session_save_failed", domain=domain, error=str(e))


async def load_session(context, domain: str) -> bool:
    """
    Load browser session for a domain.

    Args:
        context: Playwright browser context
        domain: Domain name to load session for

    Returns:
        True if session was loaded, False otherwise
    """
    try:
        session_file = get_session_file(domain)
        if not session_file.exists():
            logger.debug("session_not_found", domain=domain)
            return False

        with open(session_file, "r") as f:
            session_data = json.load(f)

        cookies = session_data.get("cookies", [])
        if cookies:
            await context.add_cookies(cookies)
            logger.info("session_loaded", domain=domain, cookie_count=len(cookies))
            return True

        return False
    except Exception as e:
        logger.error("session_load_failed", domain=domain, error=str(e))
        return False
