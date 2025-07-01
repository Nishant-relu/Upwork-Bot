import logging
from bs4 import BeautifulSoup
from ..selectors import ActivitySelectors


logger = logging.getLogger(__name__)


class ActivityParser:
    @staticmethod
    def parse(html: str) -> dict:
        """
        Extracts activity stats from job HTML.
        """
        activity_data = {}
        try:
            soup = BeautifulSoup(html, 'lxml')
            activity_list_tag = soup.find_all(*ActivitySelectors.ACTIVITY_LIST_TAG)

            if not activity_list_tag:
                logger.info("No activity tags found.")
                return activity_data

            for li_tag in activity_list_tag:
                try:
                    title = li_tag.find(*ActivitySelectors.ACTIVITY_TITLE_TAG).text.strip()
                    value = li_tag.find(*ActivitySelectors.ACTIVITY_TITLE_VALUE_TAG).text.strip()

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
                    logger.warning(f"Failed to parse activity item: {e}", exc_info=True)

            logger.info(f"Extracted activity data: {activity_data}")
        except Exception as e:
            logger.error(f"Error parsing activity section: {e}", exc_info=True)
        
        return activity_data
