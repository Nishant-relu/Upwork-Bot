import json
import logging
import random
from pathlib import Path

from patchright.async_api import Page

from auth import UpworkLoginManager
from browser import handle_captcha, dismiss_cookies_popup
from config import paths, bot_settings
from upwork.parser import JobHtmlParser
from utils import save_job_filter_stats


logger = logging.getLogger(__name__)

class Filter1:

    def __init__(self, job_data_file:Path):
        self.JOB_DATA_FILE = job_data_file or paths.APPLIED_JOBS_DIR / 'job_data.txt'
    
    async def check_url_exists(self, url:str) -> bool:
        """
        Check whether a job URL has already been processed.
        """
        try:
            with open(self.JOB_DATA_FILE, mode="r") as f:
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
        
        if self.check_url_exists(link):
            self.counters['skipped_existing'] +=1

            logger.info(f"Skipped link : {link} \n Link already exists in db.\n\n")
            return False
        else:
            self.counters['unique_jobs'] += 1
        
        if cost < settings.MIN_BUDGET:
            self.counters['skipped_filter1']['total'] += 1
            self.counters['skipped_filter1']['cost'] += 1

            self.save_url(job_data['link'], f"cost: {cost} is less than fixed cost:{settings.MIN_BUDGET}")
            logger.info("Link saved to text File.")
            logger.info(
                f"Skipped link : {link} "
                f"\nLink skipped as cost: {cost} is less than fixed cost:{settings.MIN_BUDGET}.\n\n")
            return False
        
        for keyword in settings.SKIPPED_KEYWORDS or ['Lead Generation']:
            if keyword in job_data.get('keywords', []):
                self.counters['skipped_filter1']['total'] += 1
                self.counters['skipped_filter1']['keyword'] += 1

                self.save_url(job_data['link'], f"Contains keyword: {keyword}")
                logger.info("Link saved to text File.")
                logger.info(f"Skipped link : {link} \nLink is skipped as its Skills section contains {keyword}.\n\n")
                return False
        
        return True
    