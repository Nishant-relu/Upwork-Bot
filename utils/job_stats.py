import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from config import paths
from services.google_service import batch_append_jobs, batch_update_by_key
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

INDIA_TZ = ZoneInfo("Asia/Kolkata")

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
                url_line = f"{datetime.now(INDIA_TZ).strftime('%Y-%m-%d %H:%M:%S')} | {url}"
                f.write(f"{url_line}\n({reason})\n" if reason else f"{url_line}\n")

    except Exception as e:
        logger.error(f"Error occurred while saving URL: {url} | {e}", exc_info=True)


async def save_job_apply_stats(user:str, url:str, invitation_job:bool=False):
    """Save per day applied jobs stats"""
    try:
        file_path = paths.APPLIED_JOBS_DIR / f"jobs_applied_{datetime.now(INDIA_TZ).date()}.json"
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
        file_path = paths.APPLIED_JOBS_DIR / f"filtered_jobs_stats_{datetime.now(INDIA_TZ).date()}.json"
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
                'max_proposal': 0,
                'location': 0
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


async def save_scraped_jobs(jobs_data:list[dict], file_dir:Path|None=None):

    try:
        if file_dir:
            file_path = file_dir / f"scraped_jobs_{datetime.now().date()}.json"
        else:
            file_path = paths.SCRAPED_JOBS_DIR / f"scraped_jobs_{datetime.now(INDIA_TZ).date()}.json"

        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    existing_job = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"JSON decode failed for {file_path}, initializing empty list.")
                existing_job = []
        else:
            existing_job = []

        existing_link = { job.get("link") for job in existing_job }
        unique_job = [job for job in jobs_data if job.get("link") not in existing_link]

        if unique_job:
            updated_jobs = unique_job + existing_job

            with open(file_path, 'w') as f:
                json.dump(updated_jobs, f, indent=4)
            
            logger.info(f"Saved {len(unique_job)} new job(s) to {file_path}")
        else:
            logger.info("No new unique jobs to save.")
    
    except Exception as e:
        logger.error(f"Error while saving scraped data: {e}", exc_info=True)

async def deduplicate_scraped_jobs(jobs_data:list[dict]) -> list[dict] | list:
    """Deduplicate scraped jobs based on job link."""
    try:
        unique_jobs = []
        with open(paths.APPLIED_JOBS_FILE, 'r') as f:
            applied_links = {line.strip() for line in f if line.strip() and not line.startswith('(')}
        
        for job in jobs_data:
            link = job.get("link")
            if link and link not in applied_links:
                unique_jobs.append(job)
        
        logger.info(f"Deduplicated jobs: {len(jobs_data)} -> {len(unique_jobs)}")
        return unique_jobs
    except Exception as e:
        logger.error(f"Error during deduplication: {e}", exc_info=True)
        return jobs_data

async def save_jobs_to_sheet(jobs_data:list[dict]):
    """Save scraped jobs data to Google Sheets"""
    try:
        from config import bot_settings
        spreadsheet_id = bot_settings.SPREADSHEET_ID
        sheet_name = bot_settings.JOBS_SHEET_NAME

        if not jobs_data:
            logger.info("No job data to save to sheet.")
            return
        
        new_jobs = await deduplicate_scraped_jobs(jobs_data)

        data = batch_append_jobs(spreadsheet_id, sheet_name, new_jobs)
        logger.info(f"Appended jobs to Google Sheet. Append response data: {data}")

    except Exception as e:
        logger.error(f"Error while saving jobs to Google Sheets: {e}", exc_info=True)

async def update_job_in_sheet(updates:list[dict]):
    """Batch update jobs in Google Sheets based on a list of updates."""
    from config import bot_settings
    spreadsheet_id = bot_settings.SPREADSHEET_ID
    sheet_name = bot_settings.JOBS_SHEET_NAME

    if not updates:
        logger.info("No updates to apply to sheet.")
        return

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            data = batch_update_by_key(spreadsheet_id, sheet_name, updates)
            logger.info(f"Updated jobs in Google Sheet. Update response data: {data}")
            return
        except Exception as e:
            logger.warning(
                f"Sheet update attempt {attempt}/{max_attempts} failed: {e}"
            )
            if attempt < max_attempts:
                await asyncio.sleep(2 * attempt)

    logger.error(
        f"Failed to update jobs in Google Sheets after {max_attempts} attempts. "
        f"{len(updates)} update(s) lost this run."
    )
