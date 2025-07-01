import logging
import re
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


def format_text(text: str) -> str:
    """Format the text by removing extra spaces and newlines."""
    return ' '.join(text.strip().replace(",","").split()) if text else ''


def format_price(text: str | None) -> float:
    """Format the price string to remove unwanted characters."""
    try:
        if not text:
            return 0.00
        match = re.search(r"(?:Est\. budget:|Hourly:)?\s*\$?(\d+(?:\.\d{1,2})?)", text)
        return float(match.group(1).replace(',', '')) if match else 0.00
    except Exception as e:
        logger.warning(f"Failed to parse price from text '{text}': {e}")
        return 0.00


def find_element(soup: BeautifulSoup, selector) -> Tag | None:
    """Find an element in the soup using the selector."""
    tag, attrs = selector
    return soup.find(tag, attrs) if attrs else soup.find(tag)
