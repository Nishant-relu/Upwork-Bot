import json
import logging
import random
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from patchright.async_api import Page

from browser import dismiss_cookies_popup, handle_captcha
from config import bot_settings, paths
from config.schema import UserConfig
from upwork.parser import JobHtmlParser
from utils import save_job_filter_stats, save_url
from utils.job_stats import update_job_in_sheet

from .auth import UpworkLoginManager
from .selectors import UpworkJobDetailSelectors

logger = logging.getLogger(__name__)
INDIA_TZ = ZoneInfo("Asia/Kolkata")


class JobFilter:
    """ 
    Handles filtering logic for Upwork job listings based on predefined rules 
    """
    def __init__(
            self, 
            page:Page, 
            db_text_file:Path|None=None, 
            filtered_jobs_file:Path|None=None
        ):
        """Initialize with a SeleniumBase browser instance."""
        self.page = page

        self.APPLIED_JOBS_FILE = db_text_file or paths.APPLIED_JOBS_DIR / 'job_data.txt'
        self.APPLIED_JOBS_FILE.touch(exist_ok=True)

        self.FILTERED_JOBS_DATA = filtered_jobs_file or paths.FILTERED_JOBS_DIR / 'filtered_jobs.json'
    
        self.counters = {
            'total_jobs': 0,
            'skipped_existing': 0,
            'unique_jobs':0,
            'skipped_filter1': {
                'total': 0,
                'cost':0,
                'keyword': 0,
            },
            'skipped_filter2': {
                'total': 0,
                'total_spent': 0,
                'less_than_min_spent': 0,
                'hourly_rate': 0,
                'no_activity_client_data': 0,
                'no_client_data': 0,
                'proposal': 0,
                'max_proposal': 0,
                'location': 0
            },
            'total_jobs_after_filter_1':0,
            'total_jobs_after_filter_2':0
        }
        self.google_sheet_updates = []
    
    async def _fetch_page(self, url: str) -> bool | None:
        """Fetch page from the given URL with retry logic."""

        for attempt in range(1, bot_settings.MAX_RETRY+1):
            try:

                logger.info(f"Opening page: {url}")
                await self.page.goto(url, wait_until="domcontentloaded")

                if await handle_captcha(self.page):
                    await dismiss_cookies_popup(self.page)
                    return True
                
                wait_time = random.uniform(3.7, 5.93) + attempt
                logger.info(f"Retrying in {wait_time} seconds.")
                await self.page.wait_for_timeout(wait_time * 1000)
            
            except Exception as e:
                logger.warning(f"Retry {attempt + 1}: Error fetching page - {e}", exc_info=True)
                await self.page.wait_for_timeout(random.uniform(3.7, 5.93) * 1000)
        
        logger.error("Max retries exceeded while trying to fetch the page.")
        return None
    
    async def check_url_exists(self, url:str) -> bool:
        """
        Check whether a job URL has already been processed.
        """
        try:
            with open(self.APPLIED_JOBS_FILE, mode="r") as f:
                data = f.read()
                if url in data:
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"Error occurred while checking URL existence: {e}", exc_info=True)
        
    async def filter_1(self, job_data:dict) -> bool:
        """
        Apply initial filtering rules: duplicates, low budget, keywords.
        """

        link = job_data.get("link")
        cost = job_data.get('estimated_budget')
        if not cost:
            cost = 400
        
        if await self.check_url_exists(link):
            self.counters['skipped_existing'] +=1

            logger.info(f"Skipped link : {link} \n Link already exists in db.\n\n")
            return False
        else:
            self.counters['unique_jobs'] += 1
        
        if cost < bot_settings.MIN_BUDGET:
            self.counters['skipped_filter1']['total'] += 1
            self.counters['skipped_filter1']['cost'] += 1

            update = {
                "key": link,
                "values": {
                    "filter_by": "filter_1 - low budget",
                    "filter_reason": f"cost: {cost} is less than fixed cost:{bot_settings.MIN_BUDGET}",
                    "status": "skipped"
                }
            }
            self.google_sheet_updates.append(update)

            await save_url(job_data['link'], f"cost: {cost} is less than fixed cost:{bot_settings.MIN_BUDGET}")
            logger.info("Link saved to text File.")
            logger.info(
                f"Skipped link : {link} "
                f"\nLink skipped as cost: {cost} is less than fixed cost:{bot_settings.MIN_BUDGET}.\n\n")
            return False
        
        for keyword in bot_settings.SKIP_KEYWORDS or ['Lead Generation']:
            if keyword in job_data.get('keywords', []):
                self.counters['skipped_filter1']['total'] += 1
                self.counters['skipped_filter1']['keyword'] += 1

                update = {
                    "key": link,
                    "values": {
                        "filter_by": "filter_1 - forbidden keyword",
                        "filter_reason": f"Contains keyword: {keyword}",
                        "status": "skipped"
                    }
                }
                self.google_sheet_updates.append(update)

                await save_url(job_data['link'], f"Contains keyword: {keyword}")
                logger.info("Link saved to text File.")
                logger.info(f"Skipped link : {link} \nLink is skipped as its Skills section contains {keyword}.\n\n")
                return False
        
        return True
    
    async def filter_client_data(self, link:str, min_spent:int, client_data:dict) -> bool:
        """
        Filter based on client data fields.
        """
        if "total spent" not in client_data.keys():
            self.counters['skipped_filter2']['total'] += 1
            self.counters['skipped_filter2']['total_spent'] += 1

            update = {
                "key": link,
                "values": {
                    "filter_by": "filter_2 - no total spent info",
                    "filter_reason": "Total Spent info not given in About Client Data",
                    "status": "skipped"
                }
            }
            self.google_sheet_updates.append(update)

            await save_url(link, "Skipped No Total Spent info")
            logger.info(f"Skipped link: {link} ")
            logger.info("Link saved to text File.")
            logger.info("Link was skipped as Total Spent info was not given in About Client Data.\n\n")
            return False
            
        if int(client_data["total spent"]) < min_spent:
            self.counters['skipped_filter2']['total'] += 1
            self.counters['skipped_filter2']['less_than_min_spent'] += 1

            update = {
                "key": link,
                "values": {
                    "filter_by": "filter_2 - less than min total spent",
                    "filter_reason": f"Total Spent: {client_data['total spent']} is less than Min Total Spent: {min_spent}",
                    "status": "skipped"
                }
            }
            self.google_sheet_updates.append(update)

            await save_url(link, "Skipped Less Total Spent")
            logger.info(f"Skipped link: {link} ")
            logger.info("Link saved to text File.")
            logger.info(f"Link was skipped as Total Spent ({client_data['total spent']}) less than {min_spent}.\n\n")
            return False
        
        if "hourly rate" not in client_data.keys():
            self.counters['skipped_filter2']['total'] += 1
            self.counters['skipped_filter2']['hourly_rate'] += 1

            update = {
                "key": link,
                "values": {
                    "filter_by": "filter_2 - no avg. client hourly rate info",
                    "filter_reason": "Avg. Client Hourly rate info not given in About Client Data",
                    "status": "skipped"
                }
            }
            self.google_sheet_updates.append(update)

            await save_url(link, "Skipped No Avg Hourly rate")
            logger.info(f"Skipped link: {link} ")
            logger.info("Link saved to text File.")
            logger.info("Link was skipped as Client's Avg. hourly rate is not given.\n\n")
            return False

        if client_data["location"]:
            banned_countries = (country.lower() for country in bot_settings.SKIP_LOCATIONS)
            if client_data['location'].lower() in banned_countries:
                self.counters['skipped_filter2']['total'] += 1
                self.counters['skipped_filter2']['location'] += 1

                update = {
                    "key": link,
                    "values": {
                        "filter_by": "filter_2 - banned location",
                        "filter_reason": f"Location: {client_data['location']} is in banned locations list.",
                        "status": "skipped"
                    }
                }
                self.google_sheet_updates.append(update)

                await save_url(link, "Skipped Banned location.")
                logger.info(f"Skipped link: {link} ")
                logger.info("Link saved to text File.")
                logger.info("Link was skipped as Location is banned.\n\n")
                return False

        return True
    
    async def filter_2(self, job_data:dict) -> dict:
        """
        Second layer of filtering using job detail page content.
        """
        link = job_data.get("link")
        await self._fetch_page(link)

        min_spent = bot_settings.MIN_TOTAL_SPENT or 5000
        data = {}
        
        # ----- Client Info -----
        try:
            client_sel = UpworkJobDetailSelectors.CLIENT_INFO_SECTION
            await self.page.wait_for_selector(client_sel, timeout=15000)
            await self.page.locator(client_sel).scroll_into_view_if_needed(timeout=15000)
            client_html = await self.page.locator(client_sel).inner_html()
            client_data = JobHtmlParser.parse_client_info(client_html)
        except Exception as e:
            screenshot_path = paths.SCREENSHOTS_DIR / f"client_not_found_{datetime.now(INDIA_TZ).strftime("%Y-%m-%d_%H:%M:%S")}.png"
            self.page.screenshot(path=screenshot_path, full_page=True, timeout=15000)
            logger.info(f"Client data not found. Screenshot saved at {screenshot_path}")
            logger.warning(f"Client data not found: {e}", exc_info=True)
            body_html = await self.page.content()
            logger.info(f"current page html: {body_html} \n")
            client_data = {}
        
        # ----- Attachments -----
        attachment_sel = UpworkJobDetailSelectors.ATTACHMENT_SECTION
        try:
            if await self.page.locator(attachment_sel).is_visible(timeout=5000):
                await self.page.locator(attachment_sel).scroll_into_view_if_needed()
                attachment_html = await self.page.locator(attachment_sel).inner_html()
                attachments = JobHtmlParser.parse_attachments(attachment_html)
            else:
                attachments = []
        except Exception as e:
            logger.warning(f"Attachment parsing failed: {e}", exc_info=True)
            attachments = []
        
        # ----- Activity Info -----
        try:
            activity_sel = UpworkJobDetailSelectors.ACTIVITY_SECTION
            await self.page.wait_for_selector(activity_sel, timeout=15000)
            await self.page.locator(activity_sel).scroll_into_view_if_needed()
            activity_html = await self.page.locator(activity_sel).inner_html()
            activity_data = JobHtmlParser.parse_activity(activity_html)
        except Exception as e:
            screenshot_path = paths.SCREENSHOTS_DIR / f"activity_not_found_{datetime.now(INDIA_TZ).strftime("%Y-%m-%d_%H:%M:%S")}.png"
            self.page.screenshot(path=screenshot_path, full_page=True, timeout=15000)
            logger.info(f"Activity data not found. Screenshot saved at {screenshot_path}")
            logger.warning(f"Activity data not found: {e}", exc_info=True)
            body_html = await self.page.content()
            logger.info(f"current page html: {body_html} \n")
            activity_data = {}

        update = {
            "key": link,
            "values": {
                "activity_data": json.dumps(activity_data),
                "client_data": json.dumps(client_data),
            }
        }
        self.google_sheet_updates.append(update)

        if not activity_data and not client_data:
            self.counters['skipped_filter2']['total'] += 1
            self.counters['skipped_filter2']['no_activity_client_data'] += 1

            update = {
                "key": link,
                "values": {
                    "filter_by": "filter_2 - no activity & client data",
                    "filter_reason": "Both Activity Data and About Client Data not found on Job Detail Page",
                    "status": "skipped"
                }
            }
            self.google_sheet_updates.append(update)

            await save_url(link, "Skipped No Activity and Client Data")
            logger.info(f"Skipped link: {link} ")
            logger.info("Link saved to text File.")
            logger.info("Link skipped as Activity & About Client Data both not found...\n\n")
            return data
        
        if activity_data and not client_data:
            self.counters['skipped_filter2']['total'] += 1
            self.counters['skipped_filter2']['no_client_data'] += 1

            update = {
                "key": link,
                "values": {
                    "filter_by": "filter_2 - no about client data",
                    "filter_reason": "About Client Data not found on Job Detail Page",
                    "status": "skipped"
                }
            }
            self.google_sheet_updates.append(update)

            await save_url(link, "Skipped No About Client Data")
            logger.info(f"Skipped link: {link} ")
            logger.info("Link saved to text File.")
            logger.info("Link was skipped as Activity Data found but About Client Data not found...\n\n")
            return data
        
        if not activity_data and client_data:
            success = await self.filter_client_data(link, min_spent, client_data)
            if not success:
                return data
        else:
            if "Proposals:" not in activity_data.keys():
                self.counters['skipped_filter2']['total'] += 1
                self.counters['skipped_filter2']['proposal'] += 1

                update = {
                    "key": link,
                    "values": {
                        "filter_by": "filter_2 - no proposals info",
                        "filter_reason": "No Proposals info found in Activity Data",
                        "status": "skipped"
                    }
                }
                self.google_sheet_updates.append(update)

                await save_url(link, "Skipped No Proposals info found.")
                logger.info(f"Skipped link: {link} ")
                logger.info("Link saved to text File.")
                logger.info("Link was skipped as Proposals info was not given in Activity Data.\n\n")
                return data
            
            if (
                activity_data["Proposals:"]["max"] > bot_settings.MAX_PROPOSAL
            ):
                self.counters['skipped_filter2']['total'] += 1
                self.counters['skipped_filter2']['max_proposal'] += 1

                update = {
                    "key": link,
                    "values": {
                        "filter_by": "filter_2 - max proposal exceeded",
                        "filter_reason": f"Max Proposals: {activity_data['Proposals:']['max']} exceeds allowed max proposals: {bot_settings.MAX_PROPOSAL}",
                        "status": "skipped"
                    }
                }
                self.google_sheet_updates.append(update)

                await save_url(link, "Skipped Max Proposal Exceeded")
                logger.info(f"Skipped link: {link} ")
                logger.info("Link saved to text File.")
                logger.info(f"Link was skipped as Proposals are {activity_data['Proposals:']['min']} to {activity_data['Proposals:']['max']}\n\n")
                return data
            
            success = await self.filter_client_data(link, min_spent, client_data)
            if not success:
                return data
        
        logger.info(f"Passed job link: {link} \n")
        
        data['activity_data'] = activity_data
        data['client_data'] = client_data
        data['link'] = link
        data['title'] = job_data.get('title')
        data['description'] = job_data.get('description')
        data['estimated_budget'] = job_data.get('estimated_budget')
        data['hourly_rate'] = job_data.get('hourly_rate')
        data['attachments'] = attachments

        update = {
            "key": link,
            "values": {
                "filter_by": "passed all filters",
                "filter_reason": "N/A",
                "status": "passed"
            }
        }
        self.google_sheet_updates.append(update)

        return data

    async def apply_filter(self, job_data:dict) -> dict:
        """
        Apply both filters on a job entry.
        """
        if not await self.filter_1(job_data):
            return {}
        return await self.filter_2(job_data)

    async def check_session_or_login(self, user:UserConfig):
        """
        Validate or login using cookies.
        """
        try:
            logger.info(f"Logging in with {user.name}'s credentials.")
            manager = UpworkLoginManager(self.page)
            return await manager.validate_or_login(user)
        except Exception as e:
            logger.error(f"Error validating cookies or login: {e}", exc_info=True)
            return False
    
    async def filter_jobs(self, jobs_data:list[dict], worker_user:UserConfig|None = None) -> list[dict]:
        """
        Apply filtering on a list of job data.
        """
        try:
            logger.info("Filtering of Jobs Data Started...")
            user  = worker_user if worker_user else bot_settings.get_worker_user()
            filtered_jobs = []

            if not jobs_data:
                logger.info("No job data found. Returning empty result.")
                return filtered_jobs
            
            self.counters['total_jobs'] = len(jobs_data)
            success = await self.check_session_or_login(user)

            if not success:
                logger.warning("Failed to login. Aborting job filtering process.")
                return filtered_jobs
            

            logger.info("Applying Filters on jobs data...")
            for job in jobs_data:
                logger.info(f"Evaluating job: {job.get('link', '')}")
                data = await self.apply_filter(job)
                if data:
                    filtered_jobs.append(data)
            
            logger.info("Updating filter stats....")
            self.counters['total_jobs_after_filter_1'] = self.counters['total_jobs'] - (
                self.counters['skipped_existing'] + self.counters['skipped_filter1']['total']
            )

            self.counters['total_jobs_after_filter_2'] = self.counters['total_jobs'] - (
                self.counters['skipped_existing'] +
                self.counters['skipped_filter1']['total'] + 
                self.counters['skipped_filter2']['total']
            )

            with open('counters.json', 'w') as f:
                json.dump(self.counters, f, indent=4)
            
            logger.info("Saving Filtered jobs stats....")
            await save_job_filter_stats(self.counters)
            if self.google_sheet_updates:
                await update_job_in_sheet(self.google_sheet_updates)

            logger.info(f"Filtering Summary: {self.counters}")
            logger.info(f"Filtered Job Data : {filtered_jobs}")

            with open(self.FILTERED_JOBS_DATA, 'w') as f:
                json.dump(filtered_jobs, f, indent=4)
            
            return filtered_jobs
            
        except Exception as e:
            logger.error(f"Error filtering jobs: {e}", exc_info=True)
            return []

if __name__ == '__main__':
    import asyncio
    from patchright.async_api import async_playwright
    # from browser import PatchrightBrowser
    from config import configure_logging
    from upwork.scraper import JobScraper
    from utils import get_proxy
    from browser.context import ContextHandler

    configure_logging()

    worker_user = bot_settings.get_worker_user()
    name = worker_user.name
    proxy = get_proxy(name)
    cookies_path = paths.COOKIES_DIR / f"{name}_cookies.json"
    
    async def main():
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(channel='chrome',headless=False, proxy=proxy)
            context = await browser.new_context()
            page = await context.new_page()

            scraper = JobScraper(page)
            all_jobs = await scraper.scrape_jobs()

        with open('scraped_data.json', 'w') as f:
            json.dump(all_jobs, f, indent=4)
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(channel='chrome',headless=False, proxy=proxy)
            context_handler = ContextHandler(browser, cookies_path)
            context = await context_handler.create()
            page = await context.new_page()
            
            filter = JobFilter(page)
            data = await filter.filter_jobs(all_jobs, worker_user)

        if data:
            with open("filtered_data_5.json", 'w') as f:
                json.dump(data, f, indent=4)
            
            print("saved filtered job data.")
        else:
            print("No filtered job data.")

    asyncio.run(main())
