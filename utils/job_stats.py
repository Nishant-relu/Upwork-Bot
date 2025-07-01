import json
import logging
from datetime import datetime
from pathlib import Path
from config import paths


logger = logging.getLogger(__name__)


async def save_url(url: str, reason: str = "", file_path:Path|None=None, debug:bool=False):
    """
    Save a job URL and optional reason for skipping to the file.
    """
    try:
        path = file_path or paths.APPLIED_JOBS_DIR / 'job_data.txt'

        if not path.exists():
            path.touch(exist_ok=True)

        with open(paths.APPLIED_JOBS_FILE, 'a') as f:
            f.write(f"{url}\n({reason})\n" if reason else f"{url}\n")
        
        if debug:
            with open(paths.FAILED_JOB_FILE, 'a') as f:
                url_line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {url}"
                f.write(f"{url_line}\n({reason})\n" if reason else f"{url_line}\n")

    except Exception as e:
        logger.error(f"Error occurred while saving URL: {url} | {e}", exc_info=True)


async def save_job_apply_stats(user:str, url:str, invitation_job:bool=False):
    """Save per day applied jobs stats"""
    try:
        file_path = paths.APPLIED_JOBS_DIR / f"jobs_applied_{datetime.now().date()}.json"
        if not file_path.exists() or file_path.read_text().strip() == "":
            stats_data:dict = {}
        else:
            try:
                stats_data:dict = json.loads(file_path.read_text())
            except json.JSONDecodeError:
                stats_data:dict = {}

        user_data:dict = stats_data.get(user, {})
            
        user_data.setdefault("jobs_applied", 0)
        user_data.setdefault("job_urls", [])
        user_data.setdefault("invitation_applied", 0)
        user_data.setdefault("invitation_job_urls", [])

        if invitation_job:
            user_data["invitation_applied"] += 1
            user_data["invitation_job_urls"].append(url)
        else:
            user_data["jobs_applied"] += 1
            user_data["job_urls"].append(url)

        stats_data[user] = user_data
        file_path.write_text(json.dumps(stats_data, indent=4))
    
    except Exception as e:
        logger.error(f"Error while saving user stats: {e}", exc_info=True)


async def merge_counters(d1:dict[str, int|dict], d2:dict[str, int|dict]) -> dict[str, int|dict]:
    """
    Recursively merge two dicts d1 and d2 that have the same structure.
    Wherever the values are dicts, dive in and merge those sub‐dicts.
    Wherever the values are numeric (int/float), sum them.
    """
    merged = {}

    for key in d1:
        # Both must have the same key set
        if key not in d2:
            raise KeyError(f"Key {key} found in first dict but not in second dict.")
        
        v1 = d1[key]
        v2 = d2[key]
        
        # If both values are dicts, merge recursively
        if isinstance(v1, dict) and isinstance(v2, dict):
            merged[key] = await merge_counters(v1, v2)
        
        # Otherwise we assume they are numbers (int/float) and sum them
        else:
            try:
                merged[key] = v1 + v2
            except TypeError:
                raise TypeError(
                    f"Values for key {key} are not both dicts or both numbers: "
                    f"{type(v1).__name__} vs {type(v2).__name__}"
                )
    return merged


async def save_job_filter_stats(counters:dict):
    try:
        file_path = paths.APPLIED_JOBS_DIR / f"filtered_jobs_stats_{datetime.now().date()}.json"
        sample_data = {
            'total_jobs': 0,
            'skipped_existing': 0,
            'unique_jobs':0,
            'skipped_filter1': {
                'total': 0,
                'cost':0,
                'keyword': 0,
            },
            'skipped_filter2': {
                'total': 0,
                'total_spent': 0,
                'less_than_min_spent': 0,
                'hourly_rate': 0,
                'no_activity_client_data': 0,
                'no_client_data': 0,
                'proposal': 0,
                'max_proposal': 0
            },
            'total_jobs_after_filter_1':0,
            'total_jobs_after_filter_2':0
        }

        if not file_path.exists():
            file_path.write_text(json.dumps(sample_data, indent=4))
        
        data = json.loads(file_path.read_text())
        
        data = await merge_counters(data, counters)

        file_path.write_text(json.dumps(data, indent=4))

    except Exception as e:
        logger.error(f"Error while saving user stats: {e}", exc_info=True)
