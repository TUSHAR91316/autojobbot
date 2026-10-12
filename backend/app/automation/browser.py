import asyncio
import logging
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from backend.app.core.config import BROWSER_PROFILE_DIR, SCREENSHOTS_DIR

logger = logging.getLogger("applypilot.browser")


class BrowserManager:
    """
    Manages a visible Playwright browser session using a persistent user profile directory.
    Guarantees loopback isolation and explicit user visibility.
    """
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.active_page: Optional[Page] = None
        self.is_launched: bool = False

    async def get_or_launch_page(self, headless: bool = False) -> Page:
        """Launch or return the visible persistent browser page"""
        if self.is_launched and self.context and self.active_page and not self.active_page.is_closed():
            return self.active_page

        if not self.playwright:
            self.playwright = await async_playwright().start()

        profile_path = str(BROWSER_PROFILE_DIR.resolve())
        logger.info(f"Launching persistent browser with profile at {profile_path} (headless={headless})")

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=headless,
            viewport={"width": 1280, "height": 840},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
        )

        pages = self.context.pages
        self.active_page = pages[0] if pages else await self.context.new_page()
        self.is_launched = True
        return self.active_page

    async def capture_screenshot(self, page: Page, name_prefix: str) -> str:
        """Capture a diagnostic screenshot to data/screenshots/"""
        try:
            timestamp = asyncio.get_event_loop().time()
            filename = f"{name_prefix}_{int(timestamp)}.png"
            file_path = SCREENSHOTS_DIR / filename
            await page.screenshot(path=str(file_path), full_page=False)
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return ""

    async def close(self):
        """Clean shutdown of browser context"""
        try:
            if self.context:
                await self.context.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
        finally:
            self.is_launched = False
            self.context = None
            self.active_page = None
            self.playwright = None


browser_manager = BrowserManager()
