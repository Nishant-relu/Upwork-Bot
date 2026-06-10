import pycountry
from logging import getLogger

logger = getLogger(__name__)


def normalize_country(name:str) -> str|None:
    """
    Normalize country name.
    """

    if not name:
        logger.error("Provide Country name.")
        return None
    
    if not isinstance(name, str):
        logger.error("Country name should be string.")
        return None
    
    try:
        country = pycountry.countries.lookup(name.strip().lower())
        if country:
            return country.name
    except LookupError:
        pass

    try:
        results = pycountry.countries.search_fuzzy(name.strip())
        if results:
            return results[0].name
    except LookupError:
        pass

    logger.warning(f"Standard country name not found for: {name}")
    return None
