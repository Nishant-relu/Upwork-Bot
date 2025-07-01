import logging
import random
from patchright.async_api import Error, Page, TimeoutError
from browser.anti_captcha import AntiCloudflare
from config import bot_settings

logger = logging.getLogger(__name__)

COOKIES_POPUP_CLOSE_BTN = 'button.onetrust-close-btn-handler[aria-label="Close"]'


async def dismiss_cookies_popup(page: Page, wait_time_range=(3.2, 5.5)) -> None:
    """
    Dismiss the cookie consent popup on websites using OneTrust, if present.
    """
    try:
        logger.info("Checking for cookie consent popup...")

        delay = random.uniform(*wait_time_range)
        await page.wait_for_timeout(delay * 1000)
        
        popup = page.locator(COOKIES_POPUP_CLOSE_BTN)

        if await popup.is_visible():
            logger.info("Cookie popup detected. Attempting to dismiss...")
            try:
                await popup.click(timeout=15000)
                logger.info("Cookie popup dismissed successfully.")
            except TimeoutError as te:
                logger.warning(f"Timeout while clicking cookie popup: {te}")
            except Error as e:
                logger.warning(f"Failed to click cookie popup: {e}")
        else:
            logger.info("No cookie popup detected.")
    except Exception as e:
        logger.error(f"Unexpected error while attempting to dismiss cookie popup: {e}", exc_info=True)


async def handle_captcha(page:Page, wait_time_range=(3.2, 5.5)) -> bool:
    """Handle Captcha if present"""
    try:
        logger.info("Checking for captcha challenge...")

        delay = random.uniform(*wait_time_range)
        await page.wait_for_timeout(delay * 1000)

        captcha_handler = AntiCloudflare(page)

        for attempt in range(1, bot_settings.MAX_RETRY+1):
            if await captcha_handler.check():
                logger.info(f"[Attempt {attempt}] Captcha detected. Attempting to bypass.")
                captcha_handler.bypass()

                sleep_duration = random.uniform(*wait_time_range) + attempt
                logger.info(f"Sleeping for {sleep_duration:.2f} seconds after captcha attempt.")
                await page.wait_for_timeout(sleep_duration * 1000)
            else:
                logger.info("No captcha found.")
                return True
        
        logger.error(f"Captcha still present after {bot_settings.MAX_RETRY} attempts.")
    
    except Exception as e:
        logger.error(f"Got unexpected exception while handling captcha | {e}", exc_info=True)
    
    return False
