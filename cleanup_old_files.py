"""
cleanup_old_files.py
Deletes bot-generated files and log folders older than 1 month.

Targets:
  - logs/<YYYY-MM-DD>/          entire date folder
  - data/applied_jobs/*.json    files whose name ends with YYYY-MM-DD
  - data/scraped_jobs/*.json    files whose name ends with YYYY-MM-DD
  - data/screenshots/*.png      files whose name contains a date (multiple formats)
                                 falls back to file mtime for undated filenames

Run daily via cron / Task Scheduler:
  Linux/Mac cron:
    0 2 * * * /usr/bin/python3 /path/to/cleanup_old_files.py >> /path/to/cleanup.log 2>&1

  Windows Task Scheduler:
    Program : python
    Arguments: C:/path/to/cleanup_old_files.py
    Schedule : Daily, e.g. 02:00
"""

import os
import re
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

# ── configuration ────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
RETENTION_DAYS = 30          # keep files newer than this many days
DRY_RUN = False              # set True to preview without deleting anything

# ── logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── helpers ──────────────────────────────────────────────────────────────────

CUTOFF: datetime = datetime.now() - timedelta(days=RETENTION_DAYS)


def is_old(dt: datetime) -> bool:
    return dt < CUTOFF


def remove_file(path: Path) -> None:
    if DRY_RUN:
        log.info(f"[DRY-RUN] would delete file  {path}")
        return
    try:
        path.unlink()
        log.info(f"Deleted file  {path}")
    except OSError as exc:
        log.warning(f"Could not delete {path}: {exc}")


def remove_dir(path: Path) -> None:
    if DRY_RUN:
        log.info(f"[DRY-RUN] would delete dir   {path}")
        return
    try:
        shutil.rmtree(path)
        log.info(f"Deleted dir   {path}")
    except OSError as exc:
        log.warning(f"Could not delete {path}: {exc}")


# Date patterns found in filenames
# Priority order matters — more specific patterns first.
_DATE_PATTERNS = [
    # YYYY-MM-DD  e.g. scraped_jobs_2025-07-07.json, activity_missing_2026-01-30_14-39-06.png
    (re.compile(r"(\d{4})-(\d{2})-(\d{2})"), "%Y-%m-%d", lambda m: (m.group(1), m.group(2), m.group(3))),
    # DDMMYYYY    e.g. login_failed_02022026_174339.png
    (re.compile(r"(\d{2})(\d{2})(\d{4})"), "%d%m%Y", lambda m: (m.group(1), m.group(2), m.group(3))),
]


def date_from_filename(name: str) -> datetime | None:
    """Return the first parseable date found in a filename, or None."""
    for pattern, fmt, _ in _DATE_PATTERNS:
        match = pattern.search(name)
        if match:
            date_str = match.group(0)
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    return None


def mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime)


# ── cleaners ─────────────────────────────────────────────────────────────────

def clean_log_folders() -> None:
    """Delete logs/<YYYY-MM-DD> directories older than the cutoff."""
    logs_dir = BASE_DIR / "logs"
    if not logs_dir.is_dir():
        log.warning(f"logs directory not found: {logs_dir}")
        return

    for entry in sorted(logs_dir.iterdir()):
        if not entry.is_dir():
            continue
        try:
            folder_date = datetime.strptime(entry.name, "%Y-%m-%d")
        except ValueError:
            log.debug(f"Skipping non-date log folder: {entry.name}")
            continue

        if is_old(folder_date):
            remove_dir(entry)


def clean_dated_json_files(folder: Path) -> None:
    """Delete *.json files in *folder* whose embedded date is older than cutoff.

    Files with no parseable date in their name are left untouched.
    """
    if not folder.is_dir():
        log.warning(f"Directory not found: {folder}")
        return

    for f in sorted(folder.glob("*.json")):
        dt = date_from_filename(f.name)
        if dt is None:
            log.debug(f"No date in filename, skipping: {f.name}")
            continue
        if is_old(dt):
            remove_file(f)


def clean_screenshot_files() -> None:
    """Delete screenshot files older than cutoff.

    Uses the date embedded in the filename when available,
    falls back to the file's modification time otherwise.
    """
    screenshots_dir = BASE_DIR / "data" / "screenshots"
    if not screenshots_dir.is_dir():
        log.warning(f"screenshots directory not found: {screenshots_dir}")
        return

    for f in sorted(screenshots_dir.iterdir()):
        if not f.is_file():
            continue
        dt = date_from_filename(f.name)
        if dt is None:
            # No date in name — use file modification time
            dt = mtime(f)
            log.debug(f"No date in filename for {f.name}, using mtime: {dt.date()}")
        if is_old(dt):
            remove_file(f)


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    log.info(f"=== Cleanup started  cutoff={CUTOFF.date()}  dry_run={DRY_RUN} ===")

    clean_log_folders()
    clean_dated_json_files(BASE_DIR / "data" / "applied_jobs")
    clean_dated_json_files(BASE_DIR / "data" / "scraped_jobs")
    clean_screenshot_files()

    log.info("=== Cleanup finished ===")


if __name__ == "__main__":
    main()
