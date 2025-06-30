import json
import logging
import random
from enum import Enum

from bs4 import BeautifulSoup
from patchright.async_api import Page

from browser.utils import dismiss_cookies_popup, handle_captcha
from config.paths import paths
from config.settings import settings
from config import constants
from upwork.parser import JobHtmlParser

logger = logging.getLogger(__name__)

class Selector(Enum):
    """Enum representing different selectors used to extract job data."""

    CARD_CONTAINER = ('section', {'class': 'card-list-container'})
    JOB_CARD = ('article', {})
    PAGE_BOTTOM = 'div.air3-card-section.d-lg-flex.justify-space-between[data-test="LazyHydrate"]'


class JobScraper:
    """A scraper class to extract job listings from Upwork."""

    def __init__(self, page:Page):
        """Initialize with a SeleniumBase browser instance."""
        self.page = page
    
    async def save_to_json(self, dict_data: dict, filename: str):
        """
        Save scraped data to a JSON file.
        """
        try:
            with open(paths.SCRAPED_JOBS_DIR / filename, "w", encoding="utf-8") as f:
                json.dump(dict_data, f, indent=4)
            logger.info(f"Scraped Jobs Data saved to {paths.SCRAPED_JOBS_DIR / filename}")
        except Exception as e:
            logger.error(f"Error saving data to JSON: {e}", exc_info=True)

    async def _fetch_page(self, url: str) -> str | None:
        """Fetch HTML page source from the given URL with retry logic."""

        for attempt in range(1, settings.MAX_RETRY+1):
            try:
                await self.page.goto(url, wait_until="domcontentloaded")

                if await handle_captcha(self.page):

                    await dismiss_cookies_popup(self.page)

                    await self.page.locator(Selector.PAGE_BOTTOM.value).scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(random.uniform(3500, 5500))

                    page_source = await self.page.content()
                    return page_source
                
                await self.page.wait_for_timeout(random.uniform(3500, 5500))
            except Exception as e:
                logger.warning(f"Retry {attempt + 1}: Error fetching page - {e}")
                await self.page.wait_for_timeout(random.uniform(3000, 5000))
        
        logger.error("Max retries exceeded while fetching page.")
        return None
    
    async def scrape_jobs(self, url: str|None = None) -> list:
        """Scrape job listings from the given URL or default Upwork job URL."""

        link = url or constants.UPWORK_JOBS_SEARCH_URL
        page_content = await self._fetch_page(link)

        if not page_content:
            logger.error("Failed to fetch page HTML.")
            return []

        logger.info("Parsing job listings from page...")
        soup = BeautifulSoup(page_content, 'lxml')
        card_container = soup.find(*Selector.CARD_CONTAINER.value)
        cards = card_container.find_all(*Selector.JOB_CARD.value) if card_container else []

        if not cards:
            logger.error("No job cards found on the page.")
            return []

        jobs = []
        for card in cards:
            job_info = JobHtmlParser.parse_job_card(card)
            if job_info:
                jobs.append(job_info)
        
        logger.info(f"Scraped Jobs : {jobs}")
        await self.save_to_json(jobs, "scraped_jobs_data.json")

        return jobs


if __name__ == "__main__":
    from browser.manager import PatchrightBrowser
    from config.logger_config import configure_logging
    from utils.proxy import get_proxy
    import asyncio

    configure_logging()

    name = "subham"
    proxy = get_proxy(name)

    async def main():
        async with PatchrightBrowser(profile_name=name, proxy=proxy) as context:
            page = context.pages[0]
            scraper = JobScraper(page)
            jobs = await scraper.scrape_jobs()
        
        if jobs:
            print(f"Scraped {len(jobs)} jobs and saved to jobs_data.json")
        else:
            print("No jobs found or failed to scrape.")
    
    asyncio.run(main())
