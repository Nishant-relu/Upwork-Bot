import logging
from bs4 import Tag
from config import constants
from ..selectors import JobCardSelectors
from .utils import format_price, format_text

logger = logging.getLogger(__name__)

class JobCardParser:
    @staticmethod
    def parse(card: Tag) -> dict | None:
        """Parses a single job card from the job listings page."""
        try:
            # Extract job details
            job_id = card['data-ev-job-uid']
            title_tag = card.find(*JobCardSelectors.TITLE)
            job_info_tag = card.find(*JobCardSelectors.JOB_INFO)
            job_description_tag = card.find(*JobCardSelectors.DESCRIPTION)
            keywords_tag = card.find(*JobCardSelectors.KEYWORDS)

            title = format_text(title_tag.text) if title_tag else None
            job_description = format_text(job_description_tag.text) if job_description_tag else None
            link = constants.UPWORK_BASE_URL + title_tag['href'] if title_tag else None

            job_type = job_info_tag.find(*JobCardSelectors.JOB_TYPE)
            job_type = format_text(job_type.text) if job_type else None

            if 'hourly' in job_type.lower():
                hourly_rate = format_price(job_type)
                job_type = "Hourly"
            else:
                hourly_rate = 0.00
            
            experience_level = job_info_tag.find(*JobCardSelectors.EXPERIENCE)
            experience_level = format_text(experience_level.text.strip()) if experience_level else None

            estimated_budget = job_info_tag.find(*JobCardSelectors.BUDGET)
            estimated_budget = format_price(
                format_text(estimated_budget.text.strip().replace(",", ""))
            ) if estimated_budget else 0.00

            duration = job_info_tag.find(*JobCardSelectors.DURATION)
            duration = format_text(duration.text.replace("Est. time:", "").strip()) if duration else None

            # Extract keywords
            keywords = []
            if keywords_tag:
                for keyword in keywords_tag.find_all('span'):
                    keywords.append(keyword.text.strip())

            job_info = {
                'job_id': f'~02{job_id}',
                'title': title,
                'link': link,
                'description': job_description,
                'job_type': job_type,
                'experience_level': experience_level,
                'estimated_budget': estimated_budget,
                'hourly_rate': hourly_rate,
                'duration': duration,
                'keywords': keywords
            }

            return job_info
        except Exception as e:
            logger.error(f"Error parsing job card: {e}", exc_info=True)
            return None
