import logging
import random

from patchright.async_api import Page

from browser import dismiss_cookies_popup, handle_captcha, validate_proxy_ip
from config import constants, bot_settings, paths
from utils import get_credentials, get_env, get_proxy

from .selectors import UpworkLoginSelectors

logger = logging.getLogger(__name__)


class UpworkLoginManager:
    """Manages the login process for Upwork"""
    def __init__(self, page:Page):
        """Initialize with a Patchright."""
        self.page = page
        self.selectors = UpworkLoginSelectors
    
    async def wait_random(self, min_sec:float=3.3, max_sec:float=6.7) -> None:
        """
        Wait for randomly.
        """
        await self.page.wait_for_timeout(random.uniform(min_sec, max_sec)*1000)

    async def handle_security_question(self, sec_answer: str) -> bool:
        """Handles Upwork security question if prompted."""
        try:
            logger.info("Attempting to answer security question...")
            await self.page.fill(self.selectors.SECURITY_ANSWER_INPUT, sec_answer)
            await self.page.click(self.selectors.LOGIN_SUBMIT_BUTTON)
            logger.info("Security answer submitted.")
            return True
        except Exception as e:
            logger.error(f"Exception during security question handling: {e}", exc_info=True)
            return False

    async def validate_login_success(self) -> bool:
        """Validates if login was successful by checking for jobs feed."""

        try:
            logger.info("Checking for login success...")
            await self.wait_random(5.79, 9.91)  # Wait for the page to load
            user_menu = await self.page.locator(self.selectors.USER_MENU_LIST_ITEM).is_visible()
            user_profile = await self.page.locator(self.selectors.USER_PROFILE).is_visible()

            if user_menu or user_profile:
                logger.info("Login successful")
                return True
            await self.page.screenshot(type="png", path=paths.SCREENSHOTS_DIR/"login_failed.png", full_page=True)
            logger.warning("Jobs feed not visible. Login might have failed.")
            return False
        except Exception as e:
            logger.error(f"Error validating login success: {e}")
            return False
    
    async def check_session_persistence(self) -> bool:
        """
        Check if session still active.
        """
        try:
            logger.info("Checking session persistence via dashboard...")

            await self.page.goto(constants.UPWORK_DASHBOARD_URL, wait_until="domcontentloaded")
            if not await handle_captcha(self.page):
                raise ValueError("Failed to bypass Captcha.")
            
            await dismiss_cookies_popup(self.page)

            return await self.validate_login_success()
        except Exception as e:
            logger.error(f"Got unexpected error while checking session persistence: {e}", exc_info=True)
            return False

    async def login_workflow(self, email: str, password: str, sec_answer: str) -> bool:
        """Full login flow with email, password, and optional security question."""
        try:
            logger.info("Running login workflow...")
            # Username entry
            await self.page.fill(self.selectors.USERNAME_INPUT, email)
            await self.page.click(self.selectors.CONTINUE_TO_PASSWORD_BUTTON)
            await self.wait_random(3.9, 5.47)
            
            # Password entry
            await self.page.fill(self.selectors.PASSWORD_INPUT, password)
            await self.page.click(self.selectors.REMEMBER_ME_CHECKBOX)
            await self.page.click(self.selectors.LOGIN_SUBMIT_BUTTON)
            await self.wait_random(3.9, 5.47)

            # Security question handling
            if await self.page.locator(self.selectors.SECURITY_ANSWER_INPUT).is_visible():
                logger.info("Security question detected")
                await self.handle_security_question(sec_answer)

            return await self.validate_login_success()
            
        except Exception as e:
            logger.error(f"Login workflow failed: {e}", exc_info=True)
            return False
    
    async def login(self, email: str, password: str, sec_answer: str) -> bool:
        """Standard Login Procedure"""
        for attempt in range(1, bot_settings.MAX_RETRY+1):
            try:
                # Navigate to login page
                await self.page.goto(constants.UPWORK_LOGIN_URL)
                if not await handle_captcha(self.page):
                    raise ValueError("Failed to bypass Captcha.")

                # check if already logged in
                if attempt > 1 and await self.validate_login_success():
                    return True

                if await self.login_workflow(email, password, sec_answer):
                    return True
                else:
                    logger.warning(f"Login attempt {attempt} failed. Retrying...")
                    await self.page.wait_for_timeout(random.uniform(3000, 5000))
                
            except Exception as e:
                logger.error(f"Critical error during login process: {e}", exc_info=True)
                logger.warning(f"Retry {attempt + 1}: Error fetching page - {e}")
                await self.page.wait_for_timeout(random.uniform(3000, 5000))
                
        logger.error("Exceeded max login retries.")
        return False
        
    async def validate_or_login(self, account_name:str):
        """Validate login using session or fallback to credentials."""

        try:
            logger.info(f"Starting login for account: {account_name}")

            # Verify proxy connection
            expected_ip = get_env(f"{account_name.upper()}_IP").strip()
            # await validate_proxy_ip(self.page, expected_ip)

            #check if session still active
            if await self.check_session_persistence():
                return True
            
            email, password, sec_answer = get_credentials(account_name)

            # Session expired, proceed with login workflow
            current_url:str = self.page.url

            if current_url.startswith(constants.UPWORK_LOGIN_URL):
                logger.info("On login page. Initiating login.")
                if await self.login_workflow(email, password, sec_answer):
                    return True
            
            elif current_url.startswith(constants.UPWORK_SIGNUP_URL):
                logger.info("On signup page. Redirecting to login.")

                await self.page.click('a[data-qa="login"]')
                if await self.login_workflow(email, password, sec_answer):
                    return True

            logger.info("Attempting standard login as fallback.")
            return await self.login(email, password, sec_answer)
        except Exception as e:
            logger.error(f"Error during login or cookie validation: {e}", exc_info=True)
            return False

if __name__ == '__main__':
    import asyncio
    from patchright.async_api import async_playwright
    from browser.context import ContextHandler
    from browser.manager import PatchrightBrowser
    from config.logger_config import configure_logging
    from utils.proxy import get_proxy
    from config import paths

    configure_logging()

    name = "subham"
    proxy = get_proxy(name)
    proxy = None
    cookies_path = paths.COOKIES_DIR / f"{name}_cookies.json"

    async def main():
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(channel='chrome',headless=False, proxy=proxy)
            context_handler = ContextHandler(browser, cookies_path)
            context = await context_handler.create()
            page = await context.new_page()
            manager = UpworkLoginManager(page)
            logged_in = await manager.validate_or_login(name)

            if logged_in:
                print("Logged into account successfully.")
            else:
                print("Failed to Login into account.")
            
            await context_handler.destroy()

    # async def main():
    #     async with PatchrightBrowser(profile_name=name) as context:
    #         page = context.pages[0]
    #         manager = UpworkLoginManager(page)
    #         logged_in = await manager.validate_or_login(name)

    #         if logged_in:
    #             print("Logged into account successfully.")
    #         else:
    #             print("Failed to Login into account.")
    
    asyncio.run(main())
