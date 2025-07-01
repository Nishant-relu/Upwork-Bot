import logging
from bs4 import BeautifulSoup
from config import constants

logger = logging.getLogger(__name__)


class InvitationParser:
    @staticmethod
    def parse(table_html: str) -> list[str]:
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
