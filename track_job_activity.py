import asyncio
import json
import logging
import random
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from patchright.async_api import Page, async_playwright

from browser.context import ContextHandler
from browser.utils import dismiss_cookies_popup, handle_captcha
from config.logger_config import configure_logging
from config.paths import paths
from config.settings import bot_settings
from services.google_service import bulk_upsert_sheet_data, filter_sheet_data
from upwork.auth import UpworkLoginManager
from upwork.parser import JobHtmlParser
from upwork.selectors.jobs_details_selectors import UpworkJobDetailSelectors
from utils.proxy import get_proxy

configure_logging()
logger = logging.getLogger(__name__)
INDIA_TZ = ZoneInfo("Asia/Kolkata")
TIMESTAMP_FMT = "%Y-%m-%d_%H-%M-%S"


async def open_page_with_retry(page: Page, url: str) -> bool:
    """
    Navigate to a URL with retry + captcha handling.

    Returns True if page successfully loaded.
    """

    for attempt in range(1, bot_settings.MAX_RETRY + 1):
        try:
            logger.info(f"[NAVIGATE] Opening: {url}")
            await page.goto(url, wait_until="domcontentloaded")

            if await handle_captcha(page):
                await dismiss_cookies_popup(page)
                return True

        except Exception:
            logger.warning(f"Attempt {attempt} failed for {url}", exc_info=True)

        wait_time = random.uniform(3.5, 6.2) + attempt
        await page.wait_for_timeout(wait_time * 1000)

    logger.error(f"Max retries exceeded for {url}")
    return False


async def extract_job_activity(page: Page) -> dict[str, Any]:
    """
    Extract activity metrics from job details page.
    """

    try:
        sel = UpworkJobDetailSelectors.ACTIVITY_SECTION
        await page.wait_for_selector(sel, timeout=15000)
        await page.locator(sel).scroll_into_view_if_needed()
        html = await page.locator(sel).inner_html()
        return JobHtmlParser.parse_activity(html)

    except Exception as e:
        screenshot = paths.SCREENSHOTS_DIR / f"activity_missing_{datetime.now(INDIA_TZ).strftime(TIMESTAMP_FMT)}.png"
        await page.screenshot(path=screenshot, full_page=True)
        logger.warning(f"Activity section missing: {e}")
        return {}


async def determine_job_active_status(page: Page) -> str:
    """
    Returns:
        "No"  → Job is no longer available
        "Yes" → Job is active
    """
    try:
        alert_locator = page.locator(
            'div.air3-alert[role="alert"] .air3-alert-content',
            has_text="no longer available"
        )

        return "No" if await alert_locator.count() > 0 else "Yes"

    except Exception as e:
        logger.warning(f"Job status check failed: {e}")
        return "Yes"


async def collect_activity_records(page: Page, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Visit each job link and collect activity data.
    """

    results = []

    for job in jobs:
        job_link = job.get("job_link")
        if not job_link:
            continue

        if not await open_page_with_retry(page, job_link):
            continue

        activity = await extract_job_activity(page)
        is_active = await determine_job_active_status(page)

        results.append({
            "job_link": job_link,
            "account_applied_by": job.get("applied_by", ""),
            "proposals": json.dumps(activity.get("Proposals:", {})),
            "last_viewed_by_client": activity.get("Last viewed by client:", ""),
            "interviewing": activity.get("Interviewing:", ""),
            "invite_sent": activity.get("Invites sent:", ""),
            "unanswered_invites": activity.get("Unanswered invites:", ""),
            "hires": activity.get("Hired:", "") or activity.get("Hires:", "") or "",
            "is_active": is_active,
        })

    return results


async def run_job_activity_tracking() -> None:
    """
    Main workflow:
    1. Fetch applied jobs from sheet
    2. Login
    3. Scrape activity
    4. Upsert results to sheet
    """

    spreadsheet_id = bot_settings.SPREADSHEET_ID
    jobs_sheet = bot_settings.JOBS_SHEET_NAME
    activity_sheet = bot_settings.ACTIVITY_SHEET_NAME

    logger.info("Fetching applied jobs from sheet")

    jobs = filter_sheet_data(spreadsheet_id, jobs_sheet, {"status": "applied"})
    if not jobs:
        logger.info("No applied jobs found.")
        return

    user = bot_settings.get_worker_user()
    proxy = get_proxy(user.name)
    cookies = paths.COOKIES_DIR / f"{user.name}_cookies.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=False, proxy=proxy)
        context_handler = ContextHandler(browser, cookies)
        context = await context_handler.create()
        page = await context.new_page()

        login_manager = UpworkLoginManager(page)
        await login_manager.validate_or_login(user)

        activity_records = await collect_activity_records(page, jobs)

        await context_handler.destroy()

    bulk_upsert_sheet_data(
        spreadsheet_id,
        activity_sheet,
        key_column="job_link",
        records=activity_records,
    )


if __name__ == '__main__':

    asyncio.run(run_job_activity_tracking())
