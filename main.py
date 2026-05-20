import asyncio
import logging

from patchright.async_api import async_playwright, TimeoutError

# from browser import PatchrightBrowser
from browser.context import ContextHandler
from config import bot_settings, paths
from config.schema import UserConfig
from upwork.apply import UpworkJobApplication
from upwork.auth import UpworkLoginManager
from upwork.filter import JobFilter
from upwork.scraper import JobScraper
from utils import get_proxy, save_job_apply_stats, save_url, predict_job, format_prediction_score
from utils.job_stats import update_job_in_sheet

logger = logging.getLogger(__name__)

google_sheet_updates: list[dict] = []

async def categorize_jobs(job_data: list[dict]) -> dict[str, list[dict]]:
    """
    Categorize jobs based on rate using USER_CONFIG priority:

    - If job["hourly_rate"] > 0 → use that
    - Else → fallback to client_data["hourly rate"]

    Only users with account_type == 'applicant' are considered.
    Job is assigned if:
        min_client_hourly_rate <= rate < max_client_hourly_rate
    """

    # Build applicant bucket dynamically
    categorized: dict[str, list[dict]] = {
        username: []
        for username, user in bot_settings.USER_CONFIG.items()
        if user.account_type.lower() == "applicant"
    }

    for job in job_data:
        try:
            # -------------------------
            # STEP 1: Decide which rate to use
            # -------------------------
            job_rate = job.get("hourly_rate", 0)
            client_rate_raw = job.get("client_data", {}).get("hourly rate")

            rate = None

            # Priority 1 → job hourly rate
            if job_rate and float(job_rate) > 0:
                rate = float(job_rate)

            # Priority 2 → client historical rate
            elif client_rate_raw is not None:
                rate = float(str(client_rate_raw).replace(",", "").strip())

            # If still no usable rate → skip job
            if rate is None:
                continue

            # -------------------------
            # STEP 2: Assign job
            # -------------------------
            for username, user in bot_settings.USER_CONFIG.items():
                if user.account_type.lower() != "applicant":
                    continue

                if user.min_client_hourly_rate <= rate < user.max_client_hourly_rate:
                    categorized[username].append(job)
                    break  # stop once assigned

        except (ValueError, TypeError):
            logger.warning(
                f"Invalid rate encountered | job_rate={job.get('hourly_rate')} "
                f"| client_rate={client_rate_raw}"
            )
            continue

    return categorized


async def extract_job_id(job_link: str) -> str:
    """ Extracts the job ID from the Upwork job link. """
    try:
        return "~" + job_link.split("~")[1].split("?")[0]
    except IndexError:
        logger.warning(f"Could not extract job ID from link: {job_link}")
        return ""


async def attempt_job_application(
        user:UserConfig,
        job:dict[str, str|list],
        job_applicator:UpworkJobApplication,
        invitation_job_apply:bool = False
    ) -> bool:

    link:str = job.get("link", "")
    if not link:
        logger.warning(f"[{user.name}] Skipping job with missing link: {job}")
        return False

    apply_link = job.get("apply_link", None)

    if apply_link is None:
        job_id = await extract_job_id(link)
        if not job_id:
            return False
        
        apply_link = f'https://www.upwork.com/nx/proposals/job/{job_id}apply/'
    

    attachments:list = job.get("attachments", [])
    attachment_link = attachments[0] if attachments else None

    fixed_price = job.get("fixed_price", None)

    logger.info(f"[{user.name}] Attempting to apply for job: {apply_link}")

    try:
        success, error = await job_applicator.job_apply(apply_link, user, attachment_link, fixed_price)
        if success:
            logger.info(f"[{user.name}] Successfully applied to {apply_link} \n\n")
            await save_url(link, f"Successfully applied for job using {user}")
            await save_job_apply_stats(user.name, link, invitation_job_apply)
            update = {
                "key": link,
                "values": {
                    "status": "applied",
                    "applied_by": user.name
                }
            }
            google_sheet_updates.append(update)
            return True

        update = {
            "key": link,
            "values": {
                "status": "application_failed",
                "applied_by": user.name,
                # "apply_failed_reason": error
            }
        }
        google_sheet_updates.append(update)

        await save_url(link, f"Failed to apply for job using {user.name}", debug=True)
        logger.warning(f"[{user.name}] Failed to apply to {apply_link} \n\n")
        return False
    except Exception as e:
        logger.error(f"[{user.name}] Error while applying to {apply_link}: {e}", exc_info=True)
        return False


# async def process_invitation_jobs_for_user(
#         user:str, 
#         page:Page, 
#         job_applicator:UpworkJobApplication
#     ) -> None:
#     """
#     Find and apply invitation for given user.
#     """
#     try:
#         invitor = UpworkInvite(page)
#         job_invitations = invitor.get_invitation_job_details()

#         if not job_invitations:
#             logger.info(f"No Invitation found for user: {user}")
#             return
        
#         for job in job_invitations:
#             await attempt_job_application(user, job, job_applicator, invitation_job_apply=True)
        
#     except Exception as e:
#         logger.error(f"Got an error while processing invitations for user: {user} | {e}", exc_info=True)


async def process_jobs_for_user(user_name: str, jobs:list[dict]) -> None:
    """ Applies to a list of jobs for a given user. """

    if not jobs:
        logger.info(f"No jobs to apply for user: {user_name}")
        return

    user = bot_settings.USER_CONFIG.get(user_name)
    # proxy = get_proxy(user)
    proxy = None
    cookies_path = paths.COOKIES_DIR / f"{user.name}_cookies.json"

    try:
        async with async_playwright() as playwright:
            logger.info(f"Processing jobs for user: {user.name}")

            browser = await playwright.chromium.launch(channel='chrome',headless=False, proxy=proxy)
            context_handler = ContextHandler(browser, cookies_path)
            context = await context_handler.create()
            page = await context.new_page()

            login_manager = UpworkLoginManager(page)
            await login_manager.validate_or_login(user)

            job_applicator = UpworkJobApplication(page)

            if jobs:
                for job in jobs:
                    await attempt_job_application(user, job, job_applicator)
            else:
                logger.info(f"No jobs to apply for user: {user.name}")
            
            await context_handler.destroy()
            # logger.info("Processing Invitations.")
            # await process_invitation_jobs_for_user(user, page, job_applicator)
            
    except Exception as e:
        logger.error(f"Error processing jobs for user '{user.name}': {e}", exc_info=True)


async def ml_filter_jobs(filtered_jobs: list[dict]) -> list[dict]:
    """
    Third filtering layer using the ML prediction API.
    Only jobs with probability >= 80% are passed through for application.
    Stores raw API response and formatted percentage in Google Sheets for all jobs.
    """
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
            logger.warning(f"ML API returned no result for job: {link} — skipping.")
            continue

        probability: float = result.get("probability", 0.0)
        raw_response: str = str(result)
        score: str = format_prediction_score(probability)

        if probability >= 0.80:
            logger.info(f"ML filter PASSED ({score}): {link}")
            passed_jobs.append(job)
            sheet_updates.append({
                "key": link,
                "values": {
                    "prediction": raw_response,
                    "prediction_score": score,
                }
            })
        else:
            logger.info(f"ML filter REJECTED ({score}, threshold 80%): {link}")
            sheet_updates.append({
                "key": link,
                "values": {
                    "prediction": raw_response,
                    "prediction_score": score,
                    "status": "skipped",
                    "filter_by": "filter_3 - ml prediction",
                    "filter_reason": f"ML prediction score {score} is below 80% threshold",
                }
            })

    if sheet_updates:
        await update_job_in_sheet(sheet_updates)

    logger.info(f"ML filter complete: {len(passed_jobs)}/{len(filtered_jobs)} job(s) passed.")
    return passed_jobs


async def scrape_and_filter_jobs(user: UserConfig | None = None) -> list[dict]:
    """
    Scrape and filter jobs from Upwork using the default or given user.
    """
    if user is None:
        user = bot_settings.get_worker_user()
    
    proxy = get_proxy(user.name)
    # proxy = None
    cookies_path = paths.COOKIES_DIR / f"{user.name}_cookies.json"
    
    try:
        all_jobs = []
        filtered_jobs = []
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(channel='chrome',headless=False, proxy=proxy)
            context = await browser.new_context()
            page = await context.new_page()
            scraper = JobScraper(page)
            all_jobs = await scraper.scrape_jobs()

            if not all_jobs:
                logger.info("No jobs scraped.")
                return []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(channel='chrome',headless=False, proxy=proxy)
            context_handler = ContextHandler(browser, cookies_path)
            context = await context_handler.create()
            page = await context.new_page()

            job_filter = JobFilter(page)
            filtered_jobs = await job_filter.filter_jobs(all_jobs, user)

            await context_handler.destroy()

            return filtered_jobs or []
    except TimeoutError as err:
        logger.error(f"Got an timeout error while scraping/ filtering for user '{user.name}': {err}", exc_info=True)
        return filtered_jobs or []
    except Exception as e:
        logger.error(f"Error during job scraping/filtering for user '{user.name}': {e}", exc_info=True)
        return filtered_jobs or []


async def main():
    """
    Main function to execute the Upwork automation workflow:
    - Scrapes jobs
    - Filters them
    - Categorizes based on hourly rate
    - Applies using appropriate user account
    """

    logger.info("=============== Upwork Bot Started ===============")
    try:
        import os
        os.environ.setdefault("DISPLAY", ":1")
        # print("OS Environment: ", os.environ)

        filtered_jobs = await scrape_and_filter_jobs()

        if not filtered_jobs:
            logger.info("No filtered jobs found. Exiting.")
            return

        filtered_jobs = await ml_filter_jobs(filtered_jobs)

        if not filtered_jobs:
            logger.info("No jobs passed ML filter. Exiting.")
            return

        categorized_jobs = await categorize_jobs(filtered_jobs)

        for user_name, jobs in categorized_jobs.items():
            logger.info(f"Processing {len(jobs)} jobs for user: {user_name}")
            await process_jobs_for_user(user_name, jobs)
        
        if google_sheet_updates:
            await update_job_in_sheet(google_sheet_updates)
        
        logger.info("Upwork Bot completed all tasks successfully.")

    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}", exc_info=True)
    
    logger.info("=============== Upwork Bot Ended =============== \n\n")


if __name__ == '__main__':
    from config import configure_logging

    configure_logging()

    asyncio.run(main())
