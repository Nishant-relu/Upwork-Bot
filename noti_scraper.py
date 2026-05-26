import requests
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_URL = "https://www.upwork.com/api/v3/notification-feed/notifications/users"
PAGE_LIMIT = 50
LOOKBACK_HOURS = 24

BASE_DIR = Path(__file__).parent.resolve()
TOKENS_FILE = BASE_DIR / "tokens.json"

JOB_REGEX = re.compile(r"\[\[(https?://[^\|]+)\|([^\]]+)\]\]")


def fetch_notifications_last_24h(token: str) -> list[dict]:
    """
    Paginate through notifications and collect job/new ones
    created within the last 24 hours. Stops as soon as a
    notification older than the cutoff is encountered.
    Returns list of {title, url}.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    jobs = []
    cursor = None

    while True:
        params = {"limit": PAGE_LIMIT, "notificationType": "job/new"}
        if cursor:
            params["cursor"] = cursor

        try:
            response = requests.get(
                BASE_URL,
                headers={
                    "accept": "application/json, text/plain, */*",
                    "authorization": f"Bearer {token}",
                },
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Notification API call failed: {e}")
            break

        notifications = data.get("notifications", [])
        if not notifications:
            break

        stop = False
        for notif in notifications:
            created_ms = notif.get("created")
            if not created_ms:
                continue

            created_dt = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc)
            if created_dt < cutoff:
                stop = True
                break

            if notif.get("type") != "job/new":
                continue

            match = JOB_REGEX.search(notif.get("notificationText", ""))
            if not match:
                continue

            url, title = match.groups()
            jobs.append({"title": title.strip(), "url": url.strip()})

        if stop:
            break

        cursor = data.get("cursor")
        if not cursor:
            break

    return jobs


def load_tokens() -> dict[str, str]:
    if not TOKENS_FILE.exists():
        raise FileNotFoundError(f"Tokens file not found: {TOKENS_FILE}")

    try:
        with open(TOKENS_FILE, "r") as f:
            tokens = json.load(f)
        return tokens
    except Exception as e:
        print(f"Error loading tokens: {e}")
        raise

def dedupe_jobs_by_url(jobs: list[dict]) -> list[dict]:
    """Remove duplicate jobs based on URL while preserving order."""
    seen_urls = set()
    unique_jobs = []

    for job in jobs:
        url = job.get("url")
        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)
        unique_jobs.append(job)

    return unique_jobs

def main():
    tokens = load_tokens()
    all_jobs = []
    for name, token in tokens.items():
        print(f"Processing token for user: {name}")
        jobs = fetch_notifications_last_24h(token=token)
        print(f"Found {len(jobs)} jobs for user {name}")
        all_jobs.extend(jobs)

    print(f"Total jobs found across all users: {len(all_jobs)}")

    unique_jobs = dedupe_jobs_by_url(all_jobs)
    print(f"Unique jobs after deduplication: {len(unique_jobs)}")

    with open("jobs_latest.json", "w") as f:
        json.dump(unique_jobs, f, indent=4)


if __name__ == "__main__":
    main()
