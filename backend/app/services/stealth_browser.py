"""
Anti-detection and stealth features for web scraping.

Provides:
- Playwright stealth plugin integration
- Browser fingerprint randomization
- User agent rotation
- Viewport randomization
- Timezone and locale spoofing
"""
import random
from typing import Optional, Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)


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
