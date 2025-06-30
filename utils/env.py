import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

def get_env(key: str) -> str:
    """
    Retrieve an environment variable by key, with error handling.
    """
    try:
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"Missing required environment variable: {key}")
        logger.info(f"Loaded environment variable: {key}")
        return value
    except Exception as e:
        logger.exception(f"Error loading environment variable '{key}': {e}")
        raise
