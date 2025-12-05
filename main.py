import logging
import random
import time

from patchright.async_api import Page, async_playwright

from browser import PatchrightBrowser
from browser.context import ContextHandler
from config import bot_settings, paths
from upwork.apply import UpworkJobApplication
from upwork.auth import UpworkLoginManager
from upwork.filter import JobFilter
from upwork.scraper import JobScraper
from utils import get_proxy, save_job_apply_stats, save_url

logger = logging.getLogger(__name__)


async def categorize_jobs(job_data: list[dict]) -> dict[str, list]:
    """
    Categorize jobs based on client hourly rate.
    
    - Jobs with hourly rate > 20 go to 'muktesh'
    - Others go to 'naman'
    """
    categorized = {"muktesh": [], "naman": [], "kishan":[]}

    for job in job_data:
        client_data:dict = job.get("client_data", {})
        hourly_rate:str = client_data.get("hourly rate")
        try:
            if hourly_rate is not None:
                if float(hourly_rate) > 20:
                    categorized["muktesh"].append(job)
                elif float(hourly_rate) > 15:
                    categorized["naman"].append(job)
                else:
                    categorized["kishan"].append(job)

        except (ValueError, TypeError):
            logger.warning(f"Invalid hourly rate encountered: {hourly_rate}")
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
        user:str,
        job:dict[str, str|list],
        job_applicator:UpworkJobApplication,
        invitation_job_apply:bool = False
    ) -> bool:

    link:str = job.get("link", "")
    if not link:
        logger.warning(f"[{user}] Skipping job with missing link: {job}")
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

    logger.info(f"[{user}] Attempting to apply for job: {apply_link}")

    try:
        success = await job_applicator.job_apply(apply_link, user, attachment_link, fixed_price)
        if success:
            logger.info(f"[{user}] Successfully applied to {apply_link} \n\n")
            await save_url(link, f"Successfully applied for job using {user}")
            await save_job_apply_stats(user, link, invitation_job_apply)
            return True

        await save_url(link, f"Failed to apply for job using {user}", debug=True)
        logger.warning(f"[{user}] Failed to apply to {apply_link} \n\n")
        return False
    except Exception as e:
        logger.error(f"[{user}] Error while applying to {apply_link}: {e}", exc_info=True)
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


async def process_jobs_for_user(user: str, jobs:list[dict]) -> None:
    """ Applies to a list of jobs for a given user. """

    if not jobs:
        logger.info(f"No jobs to apply for user: {user}")
        return

    # proxy = get_proxy(user)
    proxy = None
    cookies_path = paths.COOKIES_DIR / f"{user}_cookies.json"

    try:
        async with async_playwright() as playwright:
            logger.info(f"Processing jobs for user: {user}")

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
                logger.info(f"No jobs to apply for user: {user}")
            
            await context_handler.destroy()
            # logger.info("Processing Invitations.")
            # await process_invitation_jobs_for_user(user, page, job_applicator)
            
    except Exception as e:
        logger.error(f"Error processing jobs for user '{user}': {e}", exc_info=True)


async def scrape_and_filter_jobs(user: str = "subham") -> list[dict]:
    """
    Scrape and filter jobs from Upwork using the default or given user.
    """
    proxy = get_proxy(user)
    # proxy = None
    cookies_path = paths.COOKIES_DIR / f"{user}_cookies.json"
    
    try:
        all_jobs = []
        
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
            filtered_jobs = await job_filter.filter_jobs(all_jobs)

            await context_handler.destroy()

            return filtered_jobs or []
    except Exception as e:
        logger.error(f"Error during job scraping/filtering for user '{user}': {e}", exc_info=True)
        return []


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

        categorized_jobs = await categorize_jobs(filtered_jobs)

        for user, jobs in categorized_jobs.items():
            logger.info(f"Processing {len(jobs)} jobs for user: {user}")
            await process_jobs_for_user(user, jobs)

    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}", exc_info=True)
    
    logger.info("=============== Upwork Bot Ended =============== \n\n")


if __name__ == '__main__':
    import asyncio

    from config import configure_logging

    configure_logging()

    asyncio.run(main())
