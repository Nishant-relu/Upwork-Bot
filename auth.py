import logging
import random
from enum import Enum

from patchright.async_api import Page

from browser.proxy_validation import validate_proxy_ip
from browser.utils import dismiss_cookies_popup, handle_captcha
from config import constants
from config.settings import settings
from utils.credential_provider import get_credentials
from utils.env import get_env
from utils.proxy import get_proxy

logger = logging.getLogger(__name__)


class Selectors(Enum):
    USERNAME = "#login_username"
    PASSWORD = "#login_password"
    CONTINUE_BUTTON = "#login_password_continue"
    REMEMBER_ME = 'span[data-test="checkbox-input"]'
    LOGIN_BUTTON = "#login_control_continue"
    SECURITY_ANSWER = "#login_answer"
    JOBS_FEED = 'li[data-cy="user-menu"]'
    CAPTCHA_RESPONSE_INPUT = 'input[name="cf-turnstile-response"]'


class UpworkLoginManager:
    """Manages the login process for Upwork"""
    def __init__(self, page:Page):
        """Initialize with a SeleniumBase browser instance."""
        self.page = page
    
    async def wait_random(self, min_sec:float=3.3, max_sec:float=6.7) -> None:
        """
        Wait for randomly.
        """
        await self.page.wait_for_timeout(random.uniform(min_sec * 1000, max_sec * 1000))

    async def handle_security_question(self, sec_answer: str) -> bool:
        """Handles Upwork security question if prompted."""
        try:
            logger.info("Attempting to answer security question...")
            await self.page.fill(Selectors.SECURITY_ANSWER.value, sec_answer)
            await self.page.click(Selectors.LOGIN_BUTTON.value)
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
            is_visible = await self.page.locator(Selectors.JOBS_FEED.value).is_visible()

            if is_visible:
                logger.info("Login successful")
                return True

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
            await self.page.fill(Selectors.USERNAME.value, email)
            await self.page.click(Selectors.CONTINUE_BUTTON.value)
            await self.wait_random(3.9, 5.47)
            
            # Password entry
            await self.page.fill(Selectors.PASSWORD.value, password)
            await self.page.click(Selectors.REMEMBER_ME.value)
            await self.page.click(Selectors.LOGIN_BUTTON.value)
            await self.wait_random(3.9, 5.47)

            # Security question handling
            if await self.page.locator(Selectors.SECURITY_ANSWER.value).is_visible():
                logger.info("Security question detected")
                await self.handle_security_question(sec_answer)

            return await self.validate_login_success()
            
        except Exception as e:
            logger.error(f"Login workflow failed: {e}", exc_info=True)
            return False
    
    async def login(self, email: str, password: str, sec_answer: str) -> bool:
        """Standard Login Procedure"""
        try:
            for attempt in range(1, settings.MAX_RETRY+1):
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
                
            logger.error("Exceeded max login retries.")
            return False
        except Exception as e:
            logger.error(f"Critical error during login process: {e}", exc_info=True)
            return False
        
    async def validate_or_login(self, account_name:str):
        """Validate login using session or fallback to credentials."""

        try:
            logger.info(f"Starting login for account: {account_name}")

            # Verify proxy connection
            expected_ip = get_env(f"{account_name.upper()}_IP").strip()
            await validate_proxy_ip(self.page, expected_ip)

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
    from browser.manager import PatchrightBrowser
    from config.logger_config import configure_logging
    from utils.proxy import get_proxy
    import asyncio

    configure_logging()

    name = "naman"
    proxy = get_proxy(name)

    async def main():
        async with PatchrightBrowser(profile_name=name, proxy=proxy) as context:
            page = context.pages[0]
            manager = UpworkLoginManager(page)
            logged_in = await manager.validate_or_login(name)

            if logged_in:
                print("Logged into account successfully.")
            else:
                print("Failed to Login into account.")
            # driver.cdp.sleep(100)
    
    asyncio.run(main())
