import logging
import traceback
import re
from bs4 import BeautifulSoup, Tag
from config import constants


logger = logging.getLogger(__name__)


class Selectors:
    # selectors for parsing job cards on job search page
    TITLE = ('a', {})
    JOB_INFO = ('ul', {'class': 'job-tile-info-list'})
    DESCRIPTION = ('p', {})
    KEYWORDS = ('div', {'class': 'air3-token-container'})
    JOB_TYPE = ('li', {'data-test': 'job-type-label'})
    EXPERIENCE = ('li', {'data-test': 'experience-level'})
    BUDGET = ('li', {'data-test': 'is-fixed-price'})
    DURATION = ('li', {'data-test': 'duration-label'})

    # selectors for parsing activity data
    ACTIVITY_LIST_TAG = ('li', {'class':'ca-item'})
    ACTIVITY_TITLE_TAG = ('span', {'class':'title'})
    ACTIVITY_TITLE_VALUE_TAG = (['span', 'div'], {'class':'value'})

    # selectors for parsing client data
    LOCATION = ('li', {'data-qa': 'client-location'})
    JOB_POSTING_STATS = ('li', {'data-qa': 'client-job-posting-stats'})
    TOTAL_SPENT = ('strong', {'data-qa': 'client-spend'})
    CLIENT_HIRES = ('div', {'data-qa': 'client-hires'})
    COMPANY_PROFILE = ('li', {'data-qa': 'client-company-profile'})
    COMPANY_INDUSTRY = ('strong', {'data-qa': 'client-company-profile-industry'})
    COMPANY_SIZE = ('div', {'data-qa': 'client-company-profile-size'})
    HOURLY_RATE = ('strong', {'data-qa': 'client-hourly-rate'})
    CLIENT_HOURS = ('div', {'data-qa': 'client-hours'})


class JobHtmlParser:
    """
    Parses HTML data from Upwork job pages to extract:
    - Job card data (title, description, budget, etc.)
    - Activity data (e.g., proposals, interviews)
    - Client information (e.g., location, spend, hire rate)
    """
    @staticmethod
    def _find_element(soup: BeautifulSoup, selector: Selectors) -> Tag | None:
        """Find an element in the soup using the selector."""
        tag, attrs = selector.value
        return soup.find(tag, attrs) if attrs else soup.find(tag)
    
    @staticmethod
    def _format_text(text: str) -> str:
        """Format the text by removing extra spaces and newlines."""
        return ' '.join(text.strip().split()) if text else ''
    
    @staticmethod
    def _format_price(text: str | None) -> float:
        """Format the price string to remove unwanted characters."""
        try:
            if not text:
                return 0.00
            match = re.search(r"(?:Est\. budget:|Hourly:)?\s*\$?(\d+(?:\.\d{1,2})?)", text)
            return float(match.group(1).replace(',', '')) if match else 0.00
        except Exception as e:
            logger.warning(f"Failed to parse price from text '{text}': {e}")
            return 0.00

    @staticmethod
    def parse_job_card(card:Tag) -> dict | None:
        """Parses a single job card from the job listings page."""
        try:
            # Extract job details
            job_id = card['data-ev-job-uid']
            title_tag = card.find(*Selectors.TITLE)
            job_info_tag = card.find(*Selectors.JOB_INFO)
            job_description_tag = card.find(*Selectors.DESCRIPTION)
            keywords_tag = card.find(*Selectors.KEYWORDS)

            title = JobHtmlParser._format_text(title_tag.text) if title_tag else None
            job_description = JobHtmlParser._format_text(job_description_tag.text) if job_description_tag else None
            link = constants.UPWORK_BASE_URL + title_tag['href'] if title_tag else None

            job_type = job_info_tag.find(*Selectors.JOB_TYPE)
            job_type = JobHtmlParser._format_text(job_type.text) if job_type else None

            if 'hourly' in job_type.lower():
                hourly_rate = JobHtmlParser._format_price(job_type)
                job_type = "Hourly"
            else:
                hourly_rate = 0.00
            
            experience_level = job_info_tag.find(*Selectors.EXPERIENCE)
            experience_level = JobHtmlParser._format_text(experience_level.text.strip()) if experience_level else None

            estimated_budget = job_info_tag.find(*Selectors.BUDGET)
            estimated_budget = JobHtmlParser._format_price(
                JobHtmlParser._format_text(estimated_budget.text.strip())
            ) if estimated_budget else 0.00

            duration = job_info_tag.find(*Selectors.DURATION)
            duration = JobHtmlParser._format_text(duration.text.replace("Est. time:", "").strip()) if duration else None

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
            logger.error(f"Error parsing job card: {e}")
            logger.info(traceback.format_exc())
            return None
    
    @staticmethod
    def parse_activity(html: str) -> dict:
        """
        Extracts activity stats from job HTML.
        """
        activity_data = {}
        try:
            soup = BeautifulSoup(html, 'lxml')
            activity_list_tag = soup.find_all(*Selectors.ACTIVITY_LIST_TAG)

            if not activity_list_tag:
                logger.info("No activity tags found.")
                return activity_data

            for li_tag in activity_list_tag:
                try:
                    title = li_tag.find(*Selectors.ACTIVITY_TITLE_TAG).text.strip()
                    value = li_tag.find(*Selectors.ACTIVITY_TITLE_VALUE_TAG).text.strip()

                    if 'Proposals' in title:
                        if 'to' in value:
                            min_val, max_val = map(int, value.split('to'))
                        elif 'Less than' in value:
                            min_val, max_val = 1, int(value.split()[-1])
                        elif "+" in value:
                            min_val, max_val = int(value.replace("+", "")), 1000
                        else:
                            min_val = max_val = int(value)

                        activity_data[title] = {"min": min_val, "max": max_val}
                    else:
                        activity_data[title] = value
                except Exception as e:
                    logger.warning(f"Failed to parse activity item: {e}")
                    logger.info(traceback.format_exc())

            logger.info(f"Extracted activity data: {activity_data}")
        except Exception as e:
            logger.error(f"Error parsing activity section: {e}")
            logger.info(traceback.format_exc())
        
        return activity_data

    @staticmethod
    def parse_client_info(html: str) -> dict:
        """
        Extracts client info from job HTML.
        """
        client_data = {}
        data = {}

        try:
            soup = BeautifulSoup(html, 'lxml')

            # Location Data
            location_li = soup.find(*Selectors.LOCATION)
            if location_li:
                location_key = location_li.find("strong")
                location_key = location_key.text.strip() if location_key else "Not Provided"

                location_value = location_li.find("div")
                location_value = (
                    location_value.text.strip().replace(" ", "").replace("\n", " ")
                    ) if location_value else "Not Provided"
            else:
                location_key = "Not Provided"
                location_value = "Not Provided"
            data[location_key] = location_value

            # Job Posting Stats
            job_posting_li = soup.find(*Selectors.JOB_POSTING_STATS)
            if job_posting_li:
                job_posting_key = job_posting_li.find("strong")
                job_posting_key = job_posting_key.text.strip() if job_posting_key else "Not Provided"

                job_posting_value = job_posting_li.find("div")
                job_posting_value = job_posting_value.text.strip() if job_posting_value else "Not Provided"
            else:
                job_posting_key = "Not Provided"
                job_posting_value = "Not Provided"
            
            data[job_posting_key] = job_posting_value

            # Total Spent
            total_spent_li = soup.find(*Selectors.TOTAL_SPENT)
            total_spent_key = " ".join(total_spent_li.text.strip().split()) if total_spent_li else "Not Provided"

            client_hires_li = soup.find(*Selectors.CLIENT_HIRES)
            total_spent_value = client_hires_li.text.strip() if client_hires_li else "Not Provided"

            data[total_spent_key] = total_spent_value

            # Company Profile
            company_profile_li = soup.find(*Selectors.COMPANY_PROFILE)
            if company_profile_li:
                industry_key = company_profile_li.find(
                    *Selectors.COMPANY_INDUSTRY
                    )
                industry_key = industry_key.text.strip() if industry_key else "Not Provided"

                size_value = company_profile_li.find(
                    *Selectors.COMPANY_SIZE
                    )
                size_value = size_value.text.strip() if size_value else "Not Provided"
            else:
                industry_key = "Not Provided"
                size_value = "Not Provided"
            
            data[industry_key] = size_value

            # Hourly rate
            hr_rate = soup.find(*Selectors.HOURLY_RATE)
            hr_rate_key = " ".join(hr_rate.text.strip().split()) if hr_rate else "Not Provided"

            client_hr = soup.find(*Selectors.CLIENT_HOURS)
            client_hr_value = " ".join(client_hr.text.strip().split()) if client_hr else "Not Provided"

            data[hr_rate_key] = client_hr_value

            logger.info(f"Client info before cleaning : {data}")

            # Clean and structure the extracted data
            for key, value in data.items():
                if "jobs posted" in key or "job posted" in key:
                    client_data["jobs posted"] = key.split()[0]
                    if "hire rate" in value:
                        client_data["hire rate"] = value.split()[0]
                        client_data["open job"] = value.split()[-3]
                elif "total spent" in key:
                    val = key.split()[0].replace("$", "")
                    if "K" in val:
                        client_data["total spent"] = str(int(float(val.replace("K", "")) * 1000))
                    elif "M" in val:
                        client_data["total spent"] = str(int(float(val.replace("M", "")) * 1_000_000))
                    else:
                        client_data["total spent"] = val

                    if "hires" in value:
                        client_data["hires"] = value.split()[0]
                        client_data["active"] = value.split()[-2]
                elif "hourly rate" in key.lower():
                    client_data["hourly rate"] = key.split()[0].replace("$", "")
            
            logger.info(f"Parsed client info: {client_data}")
        except Exception as e:
            logger.error(f"Error parsing client info: {e}")
            logger.info(traceback.format_exc())
        
        return client_data

    @staticmethod
    def parse_attachments(html:str) -> list:
        "extracts all the attachments"
        try:

            attachments = []
            soup = BeautifulSoup(html, 'lxml')
            li_tag = soup.find_all('li')
            for li in li_tag:
                url = constants.UPWORK_BASE_URL + li.find('a')['href']
                attachments.append(url)
            
            return attachments
        except Exception as e:
            logger.info(f"Error parsing attchments link: {e}")
            logger.info(traceback.format_exc())

    @staticmethod
    def parse_invitation_table(table_html:str) -> list:
        try:
            soup = BeautifulSoup(table_html, 'lxml')
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/nx/proposals/interview/' in href:
                    links.append(f"{constants.UPWORK_BASE_URL}{href}")
            
            return links
        except Exception as e:
            logger.info(f"Error parsing invitation table: {e}", exc_info=True)
            return []