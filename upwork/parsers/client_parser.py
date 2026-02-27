import logging
from bs4 import BeautifulSoup
from ..selectors import ClientInfoSelectors
from utils import normalize_country

logger = logging.getLogger(__name__)


class ClientInfoParser:
    @staticmethod
    def parse(html: str) -> dict:
        """
        Extracts client info from job HTML.
        """
        client_data = {}
        data: dict[str, str|int|None] = {}

        try:
            soup = BeautifulSoup(html, 'lxml')

            # Location Data
            location_li = soup.find(*ClientInfoSelectors.LOCATION)
            if location_li:
                location_key = location_li.find("strong")
                location_key = location_key.text.strip() if location_key else ""

                location_value = location_li.find("div")
                location_value = (
                    location_value.text.strip().replace(" ", "").replace("\n", " ")
                    ) if location_value else ""
            else:
                location_key = ""
                location_value = ""
            data["location"] = location_key

            # Job Posting Stats
            job_posting_li = soup.find(*ClientInfoSelectors.JOB_POSTING_STATS)
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
            total_spent_li = soup.find(*ClientInfoSelectors.TOTAL_SPENT)
            total_spent_key = " ".join(total_spent_li.text.strip().split()) if total_spent_li else "Not Provided"

            client_hires_li = soup.find(*ClientInfoSelectors.CLIENT_HIRES)
            total_spent_value = client_hires_li.text.strip() if client_hires_li else "Not Provided"

            data[total_spent_key] = total_spent_value

            # Company Profile
            company_profile_li = soup.find(*ClientInfoSelectors.COMPANY_PROFILE)
            if company_profile_li:
                industry_key = company_profile_li.find(
                    *ClientInfoSelectors.COMPANY_INDUSTRY
                    )
                industry_key = industry_key.text.strip() if industry_key else "Not Provided"

                size_value = company_profile_li.find(
                    *ClientInfoSelectors.COMPANY_SIZE
                    )
                size_value = size_value.text.strip() if size_value else "Not Provided"
            else:
                industry_key = "Not Provided"
                size_value = "Not Provided"
            
            data[industry_key] = size_value

            # Hourly rate
            hr_rate = soup.find(*ClientInfoSelectors.HOURLY_RATE)
            hr_rate_key = " ".join(hr_rate.text.strip().split()) if hr_rate else "Not Provided"

            client_hr = soup.find(*ClientInfoSelectors.CLIENT_HOURS)
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
                elif "location" in key.lower():
                    normalized_country = normalize_country(value.strip())
                    client_data["location"] = normalized_country if normalized_country else value.lower()
            
            logger.info(f"Parsed client info: {client_data}")
        except Exception as e:
            logger.error(f"Error parsing client info: {e}", exc_info=True)
        
        return client_data
