import asyncio
import json
import logging
import re
import random
from datetime import datetime, timedelta, timezone  # used in production 24h lookback

import requests
from bs4 import BeautifulSoup
from patchright.async_api import async_playwright, Page

from browser.context import ContextHandler
from browser.utils import dismiss_cookies_popup, handle_captcha
from config import bot_settings, paths
from config.schema import UserConfig
from upwork.apply import UpworkJobApplication
from upwork.auth import UpworkLoginManager
from upwork.parser import JobHtmlParser
from upwork.selectors import UpworkJobDetailSelectors
from upwork.parsers.utils import format_price as parse_price
from utils import get_proxy, save_job_apply_stats, save_url, predict_job, format_prediction_score
from utils.job_stats import update_job_in_sheet
from services.google_service import batch_append_jobs, get_sheet_data

logger = logging.getLogger(__name__)

NOTI_API_URL = "https://www.upwork.com/api/v3/notification-feed/notifications/users"
NOTI_LIMIT = 50
JOB_REGEX = re.compile(r"\[\[(https?://[^\|]+)\|([^\]]+)\]\]")

google_sheet_updates: list[dict] = []


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def parse_job_detail_html(html: str) -> dict:
    """
    Parse job-specific fields from the job listing detail page HTML.
    Selectors based on actual Upwork DOM (data-cy attributes on icon divs).
    """
    soup = BeautifulSoup(html, "lxml")
    data = {
        "description": "",
        "estimated_budget": 0.0,
        "hourly_rate": 0.0,
        "job_type": "",
        "experience_level": "",
        "duration": "",
        "keywords": [],
    }

    # Description — div[data-test="Description"] > p.text-body-sm
    try:
        desc_section = soup.find("div", attrs={"data-test": "Description"})
        if desc_section:
            p_tag = desc_section.find("p", class_="text-body-sm")
            if p_tag:
                data["description"] = p_tag.get_text(separator=" ", strip=True)
    except Exception:
        pass

    # Job type + budget/rate — detect via data-cy icon, extract price from parent <li>
    try:
        fixed_icon = soup.find("div", attrs={"data-cy": "fixed-price"})
        hourly_icon = soup.find("div", attrs={"data-cy": "clock-timelog"})

        if fixed_icon:
            data["job_type"] = "Fixed"
            li = fixed_icon.find_parent("li")
            if li:
                strong = li.find("strong")
                if strong:
                    data["estimated_budget"] = parse_price(
                        strong.get_text(strip=True).replace(",", "")
                    )

        elif hourly_icon:
            data["job_type"] = "Hourly"
            li = hourly_icon.find_parent("li")
            if li:
                # Two <strong> tags for range e.g. $15.00 - $35.00, take lower bound
                strongs = li.find_all("strong")
                if strongs:
                    data["hourly_rate"] = parse_price(strongs[0].get_text(strip=True))
    except Exception:
        pass

    # Experience level — data-cy="expertise" > parent <li> > <strong>
    try:
        exp_icon = soup.find("div", attrs={"data-cy": "expertise"})
        if exp_icon:
            li = exp_icon.find_parent("li")
            if li:
                strong = li.find("strong")
                if strong:
                    data["experience_level"] = strong.get_text(strip=True)
    except Exception:
        pass

    # Duration — data-cy starts with "duration" (e.g. "duration4") > parent <li> > <strong>
    try:
        dur_icon = soup.find("div", attrs={"data-cy": re.compile(r"^duration")})
        if dur_icon:
            li = dur_icon.find_parent("li")
            if li:
                strong = li.find("strong")
                if strong:
                    desktop = strong.find("span", class_="d-none")
                    data["duration"] = (desktop or strong).get_text(strip=True)
    except Exception:
        pass

    # Keywords — div.skills-list > a.air3-badge-highlight > div.air3-line-clamp
    try:
        skills_div = soup.find("div", class_="skills-list")
        if skills_div:
            data["keywords"] = [
                a.get_text(strip=True)
                for a in skills_div.find_all("a", class_="air3-badge-highlight")
                if a.get_text(strip=True)
            ]
    except Exception:
        pass

    return data


def extract_job_id_from_url(url: str) -> str:
    """Extract job ID token from Upwork job URL e.g. '~02abc123'."""
    try:
        return "~" + url.split("~")[1].split("?")[0]
    except IndexError:
        return ""


def get_existing_sheet_job_ids() -> set[str]:
    """
    Fetch all job_id values already in Google Sheet.
    Used at pipeline start to skip already-processed jobs.
    """
    try:
        rows = get_sheet_data(
            bot_settings.SPREADSHEET_ID,
            f"{bot_settings.JOBS_SHEET_NAME}!A1:Z",
        )
        return {row.get("job_id", "") for row in rows if row.get("job_id")}
    except Exception as e:
        logger.error(f"Failed to fetch existing sheet job IDs: {e}", exc_info=True)
        return set()


# ═══════════════════════════════════════════════════════════════
# PHASE 1: NOTIFICATION EXTRACTION (per applicant account)
# ═══════════════════════════════════════════════════════════════

async def get_oauth_token(user: UserConfig) -> str | None:
    """
    Launch a fresh browser for one applicant, login, extract
    oauth2_global_js_token from cookies, then close the browser.
    """
    proxy = get_proxy(user.name)
    cookies_path = paths.COOKIES_DIR / f"{user.name}_cookies.json"

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                channel="chrome", headless=False, proxy=proxy
            )
            context_handler = ContextHandler(browser, cookies_path)
            context = await context_handler.create()
            page = await context.new_page()

            login_manager = UpworkLoginManager(page)
            logged_in = await login_manager.validate_or_login(user)

            if not logged_in:
                logger.warning(f"[{user.name}] Login failed — skipping token extraction.")
                await context_handler.destroy()
                return None

            cookies = await context.cookies()
            token = next(
                (c["value"] for c in cookies if c["name"] == "oauth2_global_js_token"),
                None,
            )
            await context_handler.destroy()

            if token:
                logger.info(f"[{user.name}] OAuth token extracted.")
            else:
                logger.warning(f"[{user.name}] oauth2_global_js_token not found in cookies.")

            return token

    except Exception as e:
        logger.error(f"[{user.name}] Error extracting OAuth token: {e}", exc_info=True)
        return None


def fetch_notifications(token: str) -> list[dict]:
    """
    Paginate through notifications and collect job/new ones from the last 24h.
    Stops as soon as a notification older than the cutoff is encountered.
    Returns list of {title, url}.
    """

    # ── TESTING MODE: fetch only 2 jobs per account ──────────────
    # TEST_LIMIT = 2
    # try:
    #     response = requests.get(
    #         NOTI_API_URL,
    #         headers={
    #             "accept": "application/json, text/plain, */*",
    #             "authorization": f"Bearer {token}",
    #         },
    #         params={"limit": NOTI_LIMIT, "notificationType": "job/new"},
    #         timeout=30,
    #     )
    #     response.raise_for_status()
    #     data = response.json()
    # except Exception as e:
    #     logger.error(f"Notification API call failed: {e}", exc_info=True)
    #     return []

    # jobs = []
    # for notif in data.get("notifications", []):
    #     if len(jobs) >= TEST_LIMIT:
    #         break
    #     if notif.get("type") != "job/new":
    #         continue
    #     match = JOB_REGEX.search(notif.get("notificationText", ""))
    #     if not match:
    #         continue
    #     url, title = match.groups()
    #     jobs.append({"title": title.strip(), "url": url.strip()})

    # return jobs
    # ── END TESTING MODE ─────────────────────────────────────────

    # ── PRODUCTION: 24h lookback (uncomment below, remove testing block above) ──
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    jobs = []
    cursor = None
    
    while True:
        params = {"limit": NOTI_LIMIT, "notificationType": "job/new"}
        if cursor:
            params["cursor"] = cursor
    
        try:
            response = requests.get(
                NOTI_API_URL,
                headers={
                    "accept": "application/json, text/plain, */*",
                    "authorization": f"Bearer {token}",
                },
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Notification API call failed: {e}", exc_info=True)
            break
    
        notifications = data.get("notifications", [])
        if not notifications:
            break
    
        stop = False
        for notif in notifications:
            created_ms = notif.get("created")
            if not created_ms:
                continue
            created_dt = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc)
            if created_dt < cutoff:
                stop = True
                break
            if notif.get("type") != "job/new":
                continue
            match = JOB_REGEX.search(notif.get("notificationText", ""))
            if not match:
                continue
            url, title = match.groups()
            jobs.append({"title": title.strip(), "url": url.strip()})
    
        if stop:
            break
        cursor = data.get("cursor")
        if not cursor:
            break
    
    return jobs

async def collect_all_notifications() -> list[dict]:
    """
    Loop all applicant accounts, extract OAuth token via browser,
    fetch latest notifications, merge and deduplicate by URL.
    Returns list of {title, url}.
    """
    applicants = [
        u for u in bot_settings.USER_CONFIG.values()
        if u.account_type.lower() == "applicant"
    ]

    if not applicants:
        logger.warning("No applicant accounts found in USER_CONFIG.")
        return []

    all_notifications: list[dict] = []

    for user in applicants:
        logger.info(f"Fetching notifications for: {user.name}")
        token = await get_oauth_token(user)
        if not token:
            logger.warning(f"[{user.name}] No token — skipping.")
            continue

        notifications = await asyncio.to_thread(fetch_notifications, token)
        logger.info(f"[{user.name}] {len(notifications)} job notification(s) found.")
        all_notifications.extend(notifications)

    seen: set[str] = set()
    unique: list[dict] = []
    for n in all_notifications:
        if n["url"] not in seen:
            seen.add(n["url"])
            unique.append(n)

    logger.info(f"Unique job notifications after dedup: {len(unique)}")
    return unique

def deduplicate_jobs(notifications: list[dict]) -> list[dict]:
    """Filter out notifications whose job ID already exists in the sheet."""
    existing_job_ids = get_existing_sheet_job_ids()
    return [
        n for n in notifications
        if extract_job_id_from_url(n.get("url", "")).lstrip("~") not in existing_job_ids
    ]

# ═══════════════════════════════════════════════════════════════
# PHASE 2: SCRAPING (worker account)
# ═══════════════════════════════════════════════════════════════

async def _fetch_page(page: Page, url: str) -> bool:
    """Navigate to URL with retry and captcha handling. Returns True on success."""
    for attempt in range(1, bot_settings.MAX_RETRY + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if await handle_captcha(page):
                await dismiss_cookies_popup(page)
                return True
            wait_time = random.uniform(3.5, 6.0) + attempt
            await page.wait_for_timeout(wait_time * 1000)
        except Exception as e:
            logger.warning(f"Attempt {attempt}: error fetching {url} — {e}")
            await page.wait_for_timeout(random.uniform(3000, 5000))

    logger.error(f"Max retries exceeded for: {url}")
    return False


async def scrape_job_page(page: Page, url: str, title: str) -> dict | None:
    """
    Navigate to one job detail page and extract all fields needed
    for filtering and application. Returns complete job dict or None.
    """
    loaded = await _fetch_page(page, url)
    if not loaded:
        return None

    # Wait for Vue.js to render job attribute elements before parsing HTML
    try:
        await page.wait_for_selector(
            "div[data-cy='fixed-price'], div[data-cy='clock-timelog']",
            timeout=15000,
        )
    except Exception:
        logger.warning(f"Job type selector not found within timeout for: {url}")

    html = await page.content()
    job_details = parse_job_detail_html(html)

    client_data: dict = {}
    try:
        client_sel = UpworkJobDetailSelectors.CLIENT_INFO_SECTION
        await page.wait_for_selector(client_sel, timeout=15000)
        client_html = await page.locator(client_sel).inner_html()
        client_data = JobHtmlParser.parse_client_info(client_html)
    except Exception as e:
        logger.warning(f"Client data not found for {url}: {e}")

    activity_data: dict = {}
    try:
        activity_sel = UpworkJobDetailSelectors.ACTIVITY_SECTION
        await page.wait_for_selector(activity_sel, timeout=15000)
        activity_html = await page.locator(activity_sel).inner_html()
        activity_data = JobHtmlParser.parse_activity(activity_html)
    except Exception as e:
        logger.warning(f"Activity data not found for {url}: {e}")

    attachments: list = []
    try:
        attachment_sel = UpworkJobDetailSelectors.ATTACHMENT_SECTION
        if await page.locator(attachment_sel).is_visible(timeout=5000):
            attachment_html = await page.locator(attachment_sel).inner_html()
            attachments = JobHtmlParser.parse_attachments(attachment_html)
    except Exception as e:
        logger.warning(f"Attachment parsing failed for {url}: {e}")

    return {
        "job_id": extract_job_id_from_url(url),
        "title": title,
        "link": url,
        "description": job_details.get("description", ""),
        "job_type": job_details.get("job_type", ""),
        "estimated_budget": job_details.get("estimated_budget", 0.0),
        "hourly_rate": job_details.get("hourly_rate", 0.0),
        "experience_level": job_details.get("experience_level", ""),
        "duration": job_details.get("duration", ""),
        "keywords": job_details.get("keywords", []),
        "client_data": client_data,
        "activity_data": activity_data,
        "attachments": attachments,
    }


async def scrape_new_jobs(
    notifications: list[dict]
) -> list[dict]:
    """
    Open worker browser, visit each notification URL not already in sheet,
    scrape all fields, save to Google Sheet.
    Returns list of scraped job dicts.
    """

    if not notifications:
        logger.info("No new notifications to scrape.")
        return []

    logger.info(f"Scraping {len(notifications)} new job(s) with worker account.")

    worker = bot_settings.get_worker_user()
    proxy = get_proxy(worker.name)
    cookies_path = paths.COOKIES_DIR / f"{worker.name}_cookies.json"
    scraped_jobs: list[dict] = []

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                channel="chrome", headless=False, proxy=proxy
            )
            context_handler = ContextHandler(browser, cookies_path)
            context = await context_handler.create()
            page = await context.new_page()

            login_manager = UpworkLoginManager(page)
            await login_manager.validate_or_login(worker)

            for notif in notifications:
                url = notif["url"]
                logger.info(f"Scraping: {url}")
                job = await scrape_job_page(page, url, notif["title"])
                if job:
                    scraped_jobs.append(job)
                else:
                    logger.warning(f"Failed to scrape: {url}")

            await context_handler.destroy()

    except Exception as e:
        logger.error(f"Error in scraping phase: {e}", exc_info=True)

    if scraped_jobs:
        try:
            batch_append_jobs(
                bot_settings.SPREADSHEET_ID,
                bot_settings.JOBS_SHEET_NAME,
                scraped_jobs,
            )
            logger.info(f"Saved {len(scraped_jobs)} job(s) to Google Sheet.")
        except Exception as e:
            logger.error(f"Failed to save scraped jobs to sheet: {e}", exc_info=True)

    return scraped_jobs


# ═══════════════════════════════════════════════════════════════
# PHASE 3: FILTERING (on already-parsed data, no browser needed)
# ═══════════════════════════════════════════════════════════════

async def apply_filter_1(job: dict) -> bool:
    """
    Filter 1: budget < MIN_BUDGET, forbidden keywords.
    Dedup is already handled in scraping phase (sheet check).
    """
    link = job.get("link", "")
    cost = float(job.get("estimated_budget") or 0)

    if cost and cost < bot_settings.MIN_BUDGET:
        logger.info(f"Filter 1 REJECTED (low budget ${cost}): {link}")
        google_sheet_updates.append({
            "key": link,
            "values": {
                "filter_by": "filter_1 - low budget",
                "filter_reason": f"Budget ${cost} < minimum ${bot_settings.MIN_BUDGET}",
                "status": "skipped",
            },
        })
        await save_url(link, f"Budget ${cost} < minimum ${bot_settings.MIN_BUDGET}")
        return False

    for keyword in bot_settings.SKIP_KEYWORDS or []:
        if keyword in job.get("keywords", []):
            logger.info(f"Filter 1 REJECTED (keyword '{keyword}'): {link}")
            google_sheet_updates.append({
                "key": link,
                "values": {
                    "filter_by": "filter_1 - forbidden keyword",
                    "filter_reason": f"Contains keyword: {keyword}",
                    "status": "skipped",
                },
            })
            await save_url(link, f"Contains keyword: {keyword}")
            return False

    return True


async def apply_filter_2(job: dict) -> bool:
    """
    Filter 2: client data checks — total spent, hourly rate field,
    banned location, proposal count.
    """
    link = job.get("link", "")
    client_data: dict = job.get("client_data", {})
    activity_data: dict = job.get("activity_data", {})
    min_spent = float(bot_settings.MIN_TOTAL_SPENT)

    def _reject(filter_by: str, reason: str):
        google_sheet_updates.append({
            "key": link,
            "values": {"filter_by": filter_by, "filter_reason": reason, "status": "skipped"},
        })

    if not client_data and not activity_data:
        logger.info(f"Filter 2 REJECTED (no client/activity data): {link}")
        _reject("filter_2 - no activity & client data", "Both activity and client data missing")
        await save_url(link, "No activity and client data")
        return False

    if not client_data:
        logger.info(f"Filter 2 REJECTED (no client data): {link}")
        _reject("filter_2 - no about client data", "Client data not found on job page")
        await save_url(link, "No client data")
        return False

    if "total spent" not in client_data:
        logger.info(f"Filter 2 REJECTED (no total spent): {link}")
        _reject("filter_2 - no total spent info", "Total spent not in client data")
        await save_url(link, "No total spent info")
        return False

    if float(client_data["total spent"]) < min_spent:
        logger.info(f"Filter 2 REJECTED (total spent {client_data['total spent']} < {min_spent}): {link}")
        _reject(
            "filter_2 - less than min total spent",
            f"Total spent {client_data['total spent']} < {min_spent}",
        )
        await save_url(link, f"Total spent {client_data['total spent']} < {min_spent}")
        return False

    location = client_data.get("location", "")
    if location:
        banned = {c.lower() for c in bot_settings.SKIP_LOCATIONS}
        if location.lower() in banned:
            logger.info(f"Filter 2 REJECTED (banned location '{location}'): {link}")
            _reject("filter_2 - banned location", f"Location '{location}' is banned")
            await save_url(link, f"Banned location: {location}")
            return False

    if activity_data and "Proposals:" in activity_data:
        proposals_max = activity_data["Proposals:"].get("max", 0)
        if proposals_max > bot_settings.MAX_PROPOSAL:
            logger.info(f"Filter 2 REJECTED (proposals {proposals_max} > {bot_settings.MAX_PROPOSAL}): {link}")
            _reject(
                "filter_2 - max proposal exceeded",
                f"Proposals {proposals_max} > max {bot_settings.MAX_PROPOSAL}",
            )
            await save_url(link, f"Proposals {proposals_max} > max {bot_settings.MAX_PROPOSAL}")
            return False

    return True


async def filter_jobs(jobs: list[dict]) -> list[dict]:
    """
    Run Filter 1 and Filter 2 on scraped jobs.
    Queues sheet updates for filter results. Returns passing jobs only.
    """
    if not jobs:
        return []

    logger.info(f"Filtering {len(jobs)} job(s)...")
    passed: list[dict] = []

    for job in jobs:
        link = job.get("link", "")
        logger.info(f"Evaluating: {link}")

        google_sheet_updates.append({
            "key": link,
            "values": {
                "activity_data": json.dumps(job.get("activity_data", {})),
                "client_data": json.dumps(job.get("client_data", {})),
            },
        })

        if not await apply_filter_1(job):
            continue
        if not await apply_filter_2(job):
            continue

        google_sheet_updates.append({
            "key": link,
            "values": {"filter_by": "passed all filters", "filter_reason": "N/A", "status": "passed"},
        })
        passed.append(job)

    logger.info(f"Filter result: {len(passed)}/{len(jobs)} job(s) passed.")
    return passed


# ═══════════════════════════════════════════════════════════════
# PHASE 4: ML FILTER
# ═══════════════════════════════════════════════════════════════

async def ml_filter_jobs(filtered_jobs: list[dict]) -> list[dict]:
    """ML prediction filter — only jobs with probability >= 75% pass."""
    if not filtered_jobs:
        logger.info("No jobs to run through ML filter.")
        return []

    logger.info(f"Running ML filter on {len(filtered_jobs)} job(s)...")
    passed_jobs: list[dict] = []
    sheet_updates: list[dict] = []

    for job in filtered_jobs:
        link = job.get("link", "")
        result = await asyncio.to_thread(predict_job, job)

        if result is None:
            logger.warning(f"ML API returned no result for: {link} — skipping.")
            continue

        probability: float = result.get("probability", 0.0)
        score: str = format_prediction_score(probability)

        if probability >= 0.75:
            logger.info(f"ML PASSED ({score}): {link}")
            passed_jobs.append(job)
            sheet_updates.append({
                "key": link,
                "values": {"prediction": str(result), "prediction_score": score},
            })
        else:
            logger.info(f"ML REJECTED ({score}): {link}")
            sheet_updates.append({
                "key": link,
                "values": {
                    "prediction": str(result),
                    "prediction_score": score,
                    "status": "skipped",
                    "filter_by": "filter_3 - ml prediction",
                    "filter_reason": f"ML score {score} below 75% threshold",
                },
            })

    if sheet_updates:
        await update_job_in_sheet(sheet_updates)

    logger.info(f"ML filter complete: {len(passed_jobs)}/{len(filtered_jobs)} passed.")
    return passed_jobs


# ═══════════════════════════════════════════════════════════════
# PHASE 5: CATEGORIZE + APPLY
# ═══════════════════════════════════════════════════════════════

async def categorize_jobs(job_data: list[dict]) -> dict[str, list[dict]]:
    """
    Assign jobs to applicant users based on hourly rate bands.
    Priority: job hourly_rate > client_data["hourly rate"].
    """
    categorized: dict[str, list[dict]] = {
        username: []
        for username, user in bot_settings.USER_CONFIG.items()
        if user.account_type.lower() == "applicant"
    }

    for job in job_data:
        try:
            job_rate = job.get("hourly_rate", 0)
            client_rate_raw = job.get("client_data", {}).get("hourly rate")
            rate = None

            if job_rate and float(job_rate) > 0:
                rate = float(job_rate)
            elif client_rate_raw is not None:
                rate = float(str(client_rate_raw).replace(",", "").strip())

            if rate is None:
                if "naman" in categorized:
                    logger.info(f"No rate found — assigning to default account 'naman': {job.get('link', '')}")
                    categorized["naman"].append(job)
                continue

            assigned = False
            for username, user in bot_settings.USER_CONFIG.items():
                if user.account_type.lower() != "applicant":
                    continue
                if user.min_client_hourly_rate <= rate < user.max_client_hourly_rate:
                    categorized[username].append(job)
                    assigned = True
                    break

            if not assigned and "naman" in categorized:
                logger.info(f"Rate ${rate} fits no band — assigning to default account 'naman': {job.get('link', '')}")
                categorized["naman"].append(job)

        except (ValueError, TypeError):
            logger.warning(
                f"Invalid rate | job_rate={job.get('hourly_rate')} "
                f"| client_rate={job.get('client_data', {}).get('hourly rate')}"
            )

    return categorized

async def attempt_job_application(
    user: UserConfig,
    job: dict[str, str | list],
    job_applicator: UpworkJobApplication,
    invitation_job_apply: bool = False,
) -> bool:
    link: str = job.get("link", "")
    if not link:
        logger.warning(f"[{user.name}] Skipping job with missing link.")
        return False

    apply_link = job.get("apply_link", None)
    if apply_link is None:
        job_id = extract_job_id_from_url(link)
        if not job_id:
            return False
        apply_link = f"https://www.upwork.com/nx/proposals/job/{job_id}/apply/"

    attachments: list = job.get("attachments", [])
    attachment_link = attachments[0] if attachments else None
    fixed_price = job.get("fixed_price", None)

    logger.info(f"[{user.name}] Applying to: {apply_link}")

    try:
        success, _ = await job_applicator.job_apply(
            apply_link, user, attachment_link, fixed_price
        )
        if success:
            logger.info(f"[{user.name}] Successfully applied to {apply_link}\n")
            await save_url(link, f"Successfully applied using {user.name}")
            await save_job_apply_stats(user.name, link, invitation_job_apply)
            google_sheet_updates.append({
                "key": link,
                "values": {"status": "applied", "applied_by": user.name},
            })
            return True

        google_sheet_updates.append({
            "key": link,
            "values": {"status": "application_failed", "applied_by": user.name},
        })
        await save_url(link, f"Failed to apply using {user.name}", debug=True)
        logger.warning(f"[{user.name}] Failed to apply to {apply_link}\n")
        return False

    except Exception as e:
        logger.error(f"[{user.name}] Error applying to {apply_link}: {e}", exc_info=True)
        return False


async def process_jobs_for_user(user_name: str, jobs: list[dict]) -> None:
    """Launch browser for one applicant user and apply to their assigned jobs."""
    if not jobs:
        logger.info(f"No jobs to apply for: {user_name}")
        return

    user = bot_settings.USER_CONFIG.get(user_name)
    proxy = None
    cookies_path = paths.COOKIES_DIR / f"{user.name}_cookies.json"

    try:
        async with async_playwright() as playwright:
            logger.info(f"Processing {len(jobs)} job(s) for: {user.name}")
            browser = await playwright.chromium.launch(
                channel="chrome", headless=False, proxy=proxy
            )
            context_handler = ContextHandler(browser, cookies_path)
            context = await context_handler.create()
            page = await context.new_page()

            login_manager = UpworkLoginManager(page)
            await login_manager.validate_or_login(user)

            job_applicator = UpworkJobApplication(page)
            for job in jobs:
                await attempt_job_application(user, job, job_applicator)

            await context_handler.destroy()

    except Exception as e:
        logger.error(f"Error processing jobs for '{user_name}': {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    logger.info("=============== Upwork Bot v2 Started ===============")

    try:
        import os
        os.environ.setdefault("DISPLAY", ":1")

        # Phase 1: collect job notifications from all applicant accounts
        notifications = await collect_all_notifications()
        if not notifications:
            logger.info("No new job notifications found. Exiting.")
            return

        # Phase 2: scrape new jobs with worker account (skip ones already in sheet)
        unique_jobs = deduplicate_jobs(notifications)
        if not unique_jobs:
            logger.info("No new unique job notifications to scrape after deduplication. Exiting.")
            return
        
        scraped_jobs = await scrape_new_jobs(unique_jobs)
        if not scraped_jobs:
            logger.info("No new jobs to process. Exiting.")
            return

        # Phase 3: filter (on already-parsed data, no browser needed)
        filtered_jobs = await filter_jobs(scraped_jobs)
        if not filtered_jobs:
            logger.info("No jobs passed filters. Exiting.")
            if google_sheet_updates:
                await update_job_in_sheet(google_sheet_updates)
            return

        # Phase 4: ML filter
        filtered_jobs = await ml_filter_jobs(filtered_jobs)
        if not filtered_jobs:
            logger.info("No jobs passed ML filter. Exiting.")
            if google_sheet_updates:
                await update_job_in_sheet(google_sheet_updates)
            return

        # Phase 5: categorize by rate band and apply per user
        categorized_jobs = await categorize_jobs(filtered_jobs)
        for user_name, jobs in categorized_jobs.items():
            logger.info(f"Processing {len(jobs)} job(s) for user: {user_name}")
            await process_jobs_for_user(user_name, jobs)

        # Flush all queued sheet updates (filter reasons, apply status)
        if google_sheet_updates:
            await update_job_in_sheet(google_sheet_updates)

        logger.info("Upwork Bot v2 completed successfully.")

    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)

    logger.info("=============== Upwork Bot v2 Ended ===============\n\n")


if __name__ == "__main__":
    from config import configure_logging
    configure_logging()
    asyncio.run(main())
