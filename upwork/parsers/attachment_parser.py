import logging
from bs4 import BeautifulSoup
from config import constants

logger = logging.getLogger(__name__)

class AttachmentParser:
    @staticmethod
    def parse(html: str) -> list[str]:
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
            logger.info(f"Error parsing attchments link: {e}", exc_info=True)
