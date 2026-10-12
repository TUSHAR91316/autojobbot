"""
Playwright Browser Automation Manager.
Controls a visible Chromium browser window on the user's desktop to automate
job applications, form filling, resume attachments, and persistent session management.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from backend.app.core.config import BROWSER_PROFILE_DIR, SCREENSHOTS_DIR

logger = logging.getLogger("applypilot.browser")


class BrowserManager:
    """
    Manages a visible Playwright browser session for live job automation.
    Supports persistent profile storage for saving real login credentials & cookies
    (LinkedIn, Indeed, Naukri, Google, etc.), as well as CDP attachment to running Chrome.
    """
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.active_page: Optional[Page] = None
        self.is_launched: bool = False
        self._lock = asyncio.Lock()
        self.is_cdp_connected: bool = False

    async def get_or_launch_page(self, headless: bool = False) -> Page:
        """Launch or return the visible browser page with persistent user profile."""
        async with self._lock:
            if self.is_launched and self.context and self.active_page:
                try:
                    if not self.active_page.is_closed():
                        await self.active_page.bring_to_front()
                        return self.active_page
                except Exception:
                    pass

            # Close any dead state
            await self._internal_close()

            if not self.playwright:
                self.playwright = await async_playwright().start()

            profile_path = str(BROWSER_PROFILE_DIR.resolve())
            logger.info(f"Launching visible browser (headless={headless}) with persistent profile at {profile_path}")

            try:
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_path,
                    headless=headless,
                    viewport={"width": 1366, "height": 860},
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-first-run",
                        "--no-default-browser-check",
                    ],
                )
            except Exception as e:
                logger.warning(f"Failed to launch with persistent profile ({e}), using session fallback: {e}")
                fallback_path = str((BROWSER_PROFILE_DIR / "session").resolve())
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=fallback_path,
                    headless=headless,
                    viewport={"width": 1366, "height": 860},
                    args=[
                        "--disable-blink-features=AutomationControlled",
                    ],
                )

            pages = self.context.pages
            self.active_page = pages[0] if pages else await self.context.new_page()
            self.is_launched = True
            self.is_cdp_connected = False
            return self.active_page

    async def connect_to_chrome_cdp(self, cdp_url: str = "http://127.0.0.1:9222") -> Page:
        """
        Connect directly to an existing Google Chrome instance started with:
        chrome.exe --remote-debugging-port=9222
        Uses the user's active, logged-in Chrome browser directly.
        """
        async with self._lock:
            await self._internal_close()
            if not self.playwright:
                self.playwright = await async_playwright().start()

            logger.info(f"Connecting to Chrome via CDP at {cdp_url}")
            browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            contexts = browser.contexts
            self.context = contexts[0] if contexts else await browser.new_context()
            pages = self.context.pages
            self.active_page = pages[0] if pages else await self.context.new_page()
            self.is_launched = True
            self.is_cdp_connected = True
            return self.active_page

    async def new_tab(self) -> Page:
        """Open and return a new browser tab in the persistent context."""
        await self.get_or_launch_page(headless=False)
        if not self.context:
            raise RuntimeError("Browser context not available")
        page = await self.context.new_page()
        self.active_page = page
        return page

    async def open_login_session(self, site: str = "linkedin") -> Dict[str, Any]:
        """
        Opens the visible desktop browser window specifically to let the user
        log in to target portals. All cookies & session state are saved in data/browser_profile.
        """
        url_map = {
            "linkedin": "https://www.linkedin.com/login",
            "indeed": "https://secure.indeed.com/account/login",
            "naukri": "https://www.naukri.com/nlogin/login",
            "wellfound": "https://wellfound.com/login",
            "google": "https://accounts.google.com",
            "portal": "http://127.0.0.1:8000/demo-career-portal",
        }
        target_url = url_map.get(site.lower(), site)
        if not target_url.startswith("http"):
            target_url = "https://" + target_url

        page = await self.get_or_launch_page(headless=False)
        await page.bring_to_front()
        await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        logger.info(f"Opened login session for '{site}' at {target_url}")

        return {
            "success": True,
            "site": site,
            "url": target_url,
            "message": f"Browser opened to {site.capitalize()}. Please sign in; your session and cookies are automatically saved!"
        }

    async def get_saved_sessions_status(self) -> Dict[str, Any]:
        """
        Check which major job portals have active authentication cookies
        stored in the persistent browser profile.
        """
        status = {
            "linkedin": False,
            "indeed": False,
            "naukri": False,
            "wellfound": False,
            "google": False,
            "total_cookies": 0,
            "profile_path": str(BROWSER_PROFILE_DIR.resolve()),
            "is_launched": self.is_launched,
            "is_cdp": self.is_cdp_connected,
        }

        if self.context:
            try:
                cookies = await self.context.cookies()
                status["total_cookies"] = len(cookies)
                domains = " ".join(c.get("domain", "").lower() for c in cookies)
                names = " ".join(c.get("name", "").lower() for c in cookies)

                status["linkedin"] = "linkedin" in domains and ("li_at" in names or "jsessionid" in names or "bcookie" in names)
                status["indeed"] = "indeed" in domains
                status["naukri"] = "naukri" in domains
                status["wellfound"] = "wellfound" in domains or "angel" in domains
                status["google"] = "google" in domains
            except Exception as e:
                logger.warning(f"Error checking cookies from active context: {e}")
        else:
            cookie_file = BROWSER_PROFILE_DIR / "Default" / "Network" / "Cookies"
            if not cookie_file.exists():
                cookie_file = BROWSER_PROFILE_DIR / "Default" / "Cookies"

            if cookie_file.exists():
                try:
                    import sqlite3
                    conn = sqlite3.connect(f"file:{cookie_file.resolve()}?mode=ro", uri=True)
                    cur = conn.cursor()
                    cur.execute("SELECT host_key, name FROM cookies")
                    rows = cur.fetchall()
                    conn.close()

                    status["total_cookies"] = len(rows)
                    domains = " ".join(r[0].lower() for r in rows)
                    names = " ".join(r[1].lower() for r in rows)

                    status["linkedin"] = "linkedin" in domains and ("li_at" in names or "jsessionid" in names or "bcookie" in names)
                    status["indeed"] = "indeed" in domains
                    status["naukri"] = "naukri" in domains
                    status["wellfound"] = "wellfound" in domains or "angel" in domains
                    status["google"] = "google" in domains
                except Exception as e:
                    logger.warning(f"Error checking offline cookies from SQLite: {e}")

        return status

    async def capture_screenshot(self, page: Optional[Page] = None, name_prefix: str = "shot") -> str:
        """Capture a diagnostic screenshot to data/screenshots/ and return web path."""
        target_page = page or self.active_page
        if not target_page:
            return ""
        try:
            timestamp = int(asyncio.get_event_loop().time() * 1000)
            filename = f"{name_prefix}_{timestamp}.png"
            SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            file_path = SCREENSHOTS_DIR / filename
            await target_page.screenshot(path=str(file_path), full_page=False)
            return f"/screenshots/{filename}"
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return ""

    async def _internal_close(self):
        """Internal teardown without lock"""
        try:
            if self.context:
                await self.context.close()
        except Exception:
            pass
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
        self.is_launched = False
        self.is_cdp_connected = False
        self.context = None
        self.active_page = None
        self.playwright = None

    async def close(self):
        """Clean shutdown of browser context"""
        async with self._lock:
            await self._internal_close()
            logger.info("Browser session closed cleanly")

    def get_status(self) -> Dict[str, Any]:
        """Current status of the browser instance"""
        is_open = self.is_launched and self.context is not None and self.active_page is not None
        return {
            "is_launched": is_open,
            "has_active_page": self.active_page is not None and not self.active_page.is_closed() if self.active_page else False,
            "is_cdp": self.is_cdp_connected,
        }


browser_manager = BrowserManager()
