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
        logger.exception(f"Standard country name not find for {name}.", exc_info=True)
        return None
