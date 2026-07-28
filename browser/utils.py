import logging
import random
from datetime import datetime

from patchright.async_api import Error, Page, TimeoutError
from browser.anti_captcha import AntiCloudflare
from config import bot_settings, paths

logger = logging.getLogger(__name__)

COOKIES_POPUP_CLOSE_BTN = 'button.onetrust-close-btn-handler[aria-label="Close"]'
SIDEBAR_OVERLAY = 'div[data-test="sidebar-overlay"]'
FTE_POPOVER = 'div[class*="ng-side-nav-fte-popover"]'
# The nav onboarding tour advances through several steps; the last one ends it.
FTE_ADVANCE_BUTTONS = ["Next", "Got it", "Done", "Finish", "Skip", "Close"]
FTE_MAX_STEPS = 8


async def dismiss_sidebar_overlay(page: Page, timeout: int = 15000) -> bool:
    """
    Clear the sidebar overlay that blocks clicks on the page.

    The overlay is raised by Upwork's redesigned-navigation onboarding tour
    ("New, simpler navigation"), which is shown once per account. It is modal:
    Escape does not close it, so the tour has to be clicked through step by step.
    While it is up, every click on the page times out even though the target
    element is visible and enabled.

    Returns True once the page is clickable again.
    """
    try:
        logger.info("Checking for sidebar overlay...")

        overlay = page.locator(SIDEBAR_OVERLAY)

        if not await overlay.count() or not await overlay.first.is_visible():
            logger.info("No sidebar overlay detected.")
            return True

        logger.info("Sidebar overlay detected. Waiting for it to clear...")

        try:
            await overlay.first.wait_for(state="hidden", timeout=timeout // 3)
            logger.info("Sidebar overlay cleared on its own.")
            return True
        except TimeoutError:
            logger.info("Sidebar overlay still present. Checking for the navigation tour.")

        if await _dismiss_fte_tour(page):
            try:
                await overlay.first.wait_for(state="hidden", timeout=timeout // 3)
                logger.info("Sidebar overlay cleared after dismissing the navigation tour.")
                return True
            except TimeoutError:
                logger.warning("Navigation tour dismissed but the overlay is still present.")

        logger.warning("Sidebar overlay still blocking the page.")
        await _capture_sidebar_overlay_state(page)
        return False

    except Exception as e:
        logger.error(f"Unexpected error while dismissing sidebar overlay: {e}", exc_info=True)
        return False


async def _dismiss_fte_tour(page: Page) -> bool:
    """
    Click through the first-time-experience navigation tour until it is gone.

    Each step shows a popover with an advance button ("Next", and "Got it" or
    similar on the final step). Returns True if the tour is no longer visible.
    """
    popover = page.locator(FTE_POPOVER)

    if not await popover.count() or not await popover.first.is_visible():
        logger.info("No navigation tour popover found.")
        return False

    logger.info("Navigation tour detected. Clicking through it.")

    for step in range(1, FTE_MAX_STEPS + 1):
        if not await popover.count() or not await popover.first.is_visible():
            logger.info(f"Navigation tour dismissed after {step - 1} step(s).")
            return True

        button = None
        for label in FTE_ADVANCE_BUTTONS:
            candidate = popover.first.get_by_role("button", name=label, exact=False)
            if await candidate.count() and await candidate.first.is_visible():
                button = candidate.first
                logger.info(f"Tour step {step}: clicking '{label}'.")
                break

        if button is None:
            logger.warning(f"Tour step {step}: no advance button found in the popover.")
            return False

        try:
            await button.click(timeout=10000)
        except (TimeoutError, Error) as e:
            logger.warning(f"Tour step {step}: failed to click advance button: {e}")
            return False

        await page.wait_for_timeout(random.uniform(1.2, 2.4) * 1000)

    logger.warning(f"Navigation tour still visible after {FTE_MAX_STEPS} steps.")
    return False


async def _capture_sidebar_overlay_state(page: Page) -> None:
    """
    Screenshot the page and log which sidebar panel is open, to identify what put it there.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot_path = paths.SCREENSHOTS_DIR / f"sidebar_overlay_blocked_{timestamp}.png"
        await page.screenshot(path=screenshot_path, full_page=True, timeout=30000, type="png")
        logger.info(f"Saved sidebar overlay screenshot: {screenshot_path}")

        blockers = await page.evaluate(
            """() => {
                const sel = '[class*="ng-side-nav-fte-popover"], [class*="fte-popover"],'
                          + ' .ng-sidebar, [class*="ng-side-nav"]';
                return Array.from(document.querySelectorAll(sel))
                    .filter(el => {
                        if (el.classList.contains('ng-sidebar-overlay')) return false;
                        if (el.classList.contains('ng-sidebar-layout-wrapper')) return false;
                        const r = el.getBoundingClientRect();
                        return r.width > 0 && r.height > 0;
                    })
                    .slice(0, 8)
                    .map(el => ({
                        cls: el.className && el.className.toString().slice(0, 120),
                        test: el.getAttribute('data-test'),
                        text: (el.innerText || '').trim().slice(0, 120),
                    }));
            }"""
        )
        logger.info(f"Visible overlay/tour element(s): {blockers}")

    except Exception as e:
        logger.warning(f"Could not capture sidebar overlay state: {e}")


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
                await captcha_handler.bypass()

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
