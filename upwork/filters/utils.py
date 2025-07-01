import logging
from pathlib import Path
from config import paths

logger = logging.getLogger(__name__)


async def save_url(url: str, reason: str = "", file_path:Path|None=None):
    """
    Save a job URL and optional reason for skipping to the file.
    """
    try:
        path = file_path or paths.APPLIED_JOBS_DIR / 'job_data.txt'

        if not path.exists():
            path.touch(exist_ok=True)
        
        with open(path, 'a') as f:
            f.write(f"{url}\n({reason})\n" if reason else f"{url}\n")
    except Exception as e:
        logger.error(f"Error occurred while saving URL: {url} | {e}", exc_info=True)
