import logging
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "upwork-bot-service-account.json"

INDIA_TZ = ZoneInfo("Asia/Kolkata")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

COLUMN_MAP: dict[str, str] = {
    "scrap_date":        "A",
    "job_id":            "B",
    "job_title":         "C",
    "job_description":   "D",
    "job_link":          "E",
    "job_type":          "F",
    "experience_level":  "G",
    "estimated_budget":  "H",
    "hourly_rate":       "I",
    "duration":          "J",
    "keywords":          "K",
    "activity_data":     "L",
    "client_data":       "M",
    "filter_by":         "N",
    "filter_reason":     "O",
    "prediction":        "P",
    "prediction_score":  "Q",
    "status":            "R",
    "applied_by":        "S",
}


def normalize_header(header: str) -> str:
    """
    Normalize Google Sheet headers:
    - Remove text inside brackets
    - Snake_case
    """
    if not header:
        return ""
    return (
        header.split("(")[0]
        .strip()
        .lower()
        .replace(" ", "_")
    )

def validate_columns(columns: Iterable[str]) -> None:
    """Ensure all columns exist in COLUMN_MAP."""
    unknown = set(columns) - COLUMN_MAP.keys()
    if unknown:
        raise ValueError(f"Unknown columns: {', '.join(unknown)}")

def normalize_job_row(job: dict[str, Any]) -> list[Any]:
    """
    Convert scraped job dict to ordered sheet row.
    """
    job_id = str(job.get("job_id", "")).replace("~", "")
    utc_now = datetime.now(timezone.utc)
    india_now = utc_now.astimezone(INDIA_TZ).strftime("%Y-%m-%d %H:%M:%S")

    return [
        india_now,
        job_id,
        job.get("title", ""),
        job.get("description", ""),
        job.get("link", ""),
        job.get("job_type", ""),
        job.get("experience_level", ""),
        job.get("estimated_budget", 0),
        job.get("hourly_rate", 0),
        job.get("duration", ""),
        ", ".join(job.get("keywords", [])),
    ]

@lru_cache(maxsize=1)
def get_google_sheets_service(
    service_account_file: Path | str = SERVICE_ACCOUNT_FILE
) -> Resource:
    """
    Create and cache Google Sheets API service.
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=SCOPES,
        )
        service = build("sheets", "v4", credentials=creds)
        logger.info("Google Sheets service initialized")
        return service
    except Exception:
        logger.exception("Failed to initialize Google Sheets service")
        raise


@lru_cache(maxsize=32)
def fetch_sheet_values(
    spreadsheet_id: str,
    range_name: str,
) -> list[list[Any]]:
    """
    Fetch raw values from a sheet range.
    """
    service = get_google_sheets_service()

    try:
        response = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueRenderOption="UNFORMATTED_VALUE",
            )
            .execute()
        )
        return response.get("values", [])
    except HttpError:
        logger.exception("Failed to fetch sheet values")
        return []


def parse_sheet_to_df(values: list[list[Any]]) -> pd.DataFrame:
    """
    Convert raw sheet values into a DataFrame.
    """
    if not values:
        return pd.DataFrame()

    headers = [normalize_header(h) for h in values[0]]
    rows = values[1:]

    return pd.DataFrame(rows, columns=headers).fillna("")


def get_sheet_data(
    spreadsheet_id: str,
    range_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch sheet data as list of dictionaries.
    """
    values = fetch_sheet_values(spreadsheet_id, range_name)
    df = parse_sheet_to_df(values)
    return df.to_dict(orient="records")


def build_row_index_by_column(
    service: Resource,
    spreadsheet_id: str,
    sheet_name: str,
    column_name: str,
) -> dict[str, int]:
    """
    Build a value -> row_number index for a column.
    """
    validate_columns([column_name])

    col = COLUMN_MAP[column_name]
    range_name = f"{sheet_name}!{col}:{col}"

    try:
        response = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )

        values = response.get("values", [])
        return {
            row[0]: idx
            for idx, row in enumerate(values, start=1)
            if row
        }
    except HttpError:
        logger.exception("Failed to build row index")
        return {}

def _batch_update(
    service: Resource,
    spreadsheet_id: str,
    data: list[dict[str, Any]],
) -> dict:
    """
    Execute batchUpdate request.
    """
    if not data:
        logger.info("No updates to apply")
        return {}

    try:
        response = (
            service.spreadsheets()
            .values()
            .batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "valueInputOption": "USER_ENTERED",
                    "data": data,
                },
            )
            .execute()
        )
        logger.info("Batch update successful | cells=%s", len(data))
        return response
    except HttpError:
        logger.exception("Batch update failed")
        raise

def update_row_by_key(
    spreadsheet_id: str,
    sheet_name: str,
    key_column: str,
    key_value: str,
    updates: dict[str, Any],
    service: Resource|None = None,
) -> dict|None:
    """
    Update columns for a single row identified by key.
    """
    validate_columns([key_column, *updates.keys()])

    service = service or get_google_sheets_service()
    row_map = build_row_index_by_column(
        service, spreadsheet_id, sheet_name, key_column
    )

    row = row_map.get(key_value)
    if not row:
        logger.warning("Row not found | %s=%s", key_column, key_value)
        return None

    data = [
        {
            "range": f"{sheet_name}!{COLUMN_MAP[col]}{row}",
            "values": [[value]],
        }
        for col, value in updates.items()
    ]

    return _batch_update(service, spreadsheet_id, data)

def batch_update_by_key(
    spreadsheet_id: str,
    sheet_name: str,
    updates: list[dict[str, Any]],
    key_column: str = "job_link",
    service: Resource|None = None,
) -> dict:
    """
    Batch update rows identified by a key column.
    """
    service = service or get_google_sheets_service()
    row_map = build_row_index_by_column(
        service, spreadsheet_id, sheet_name, key_column
    )

    data: list[dict[str, Any]] = []

    for item in updates:
        key_value = item["key"]
        values = item["values"]

        validate_columns(values.keys())

        row = row_map.get(key_value)
        if not row:
            logger.warning("Skipping missing row | %s=%s", key_column, key_value)
            continue

        for col, value in values.items():
            data.append({
                "range": f"{sheet_name}!{COLUMN_MAP[col]}{row}",
                "values": [[value]],
            })

    return _batch_update(service, spreadsheet_id, data)


def batch_append_jobs(
    spreadsheet_id: str,
    sheet_name: str,
    jobs: list[dict[str, Any]],
    service: Resource|None = None,
) -> dict:
    """
    Append multiple job rows.
    """
    if not jobs:
        logger.info("No jobs provided for append")
        return {}
    
    rows = [normalize_job_row(job) for job in jobs]
    service = service or get_google_sheets_service()

    try:
        response = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": rows},
            )
            .execute()
        )
        logger.info(f"Appended {len(rows)} job(s) to Google Sheet: {sheet_name}")
        return response
    except HttpError:
        logger.exception("Failed to append jobs")
        raise


def filter_sheet_data(
    spreadsheet_id: str,
    range_name: str,
    filters: dict,
    case_sensitive: bool = False,
) -> list[dict[str, Any]]:
    """
    Fetch sheet data and filter rows where column == value.
    """

    values = fetch_sheet_values(spreadsheet_id, range_name)
    df = parse_sheet_to_df(values)

    if df.empty:
        return []
    
    filtered_df = df.copy()

    for col, val in filters.items():

        column_name = normalize_header(col)
        if column_name not in df.columns:
            logger.warning(f"Column '{column_name}' not found in sheet")
            continue

        series = filtered_df[column_name].astype(str)
        value = str(val)

        if not case_sensitive:
            series = series.str.lower()
            value = value.lower()

        mask = series == value
        
        before_count = len(filtered_df)
        filtered_df = filtered_df[mask]
        after_count = len(filtered_df)

        logger.info(
            f"Filter applied: {column_name}={val} "
            f"(rows: {before_count} → {after_count})"
        )

        if filtered_df.empty:
            logger.info("No rows left after filtering")
            return []

    return filtered_df.to_dict(orient="records")


def bulk_upsert_sheet_data(
    spreadsheet_id: str,
    sheet_name: str,
    key_column: str,
    records: list[dict[str, Any]]
) -> None:
    """
    Bulk update or append rows in Google Sheet based on a unique key column.

    Args:
        spreadsheet_id: Google Sheet ID
        sheet_name: Name of sheet tab (e.g., "Sheet1")
        key_column: Column used as unique identifier (e.g., "job_id")
        records: List of row dicts to upsert
    """

    if not records:
        logger.info("No records provided for upsert.")
        return
    
    service = get_google_sheets_service()
    range_name = f"{sheet_name}!A1:Z"
    values = fetch_sheet_values(spreadsheet_id, range_name)

    now_str = datetime.now(INDIA_TZ).strftime("%Y-%m-%d %H:%M:%S")
    key_column_norm = normalize_header(key_column)

    if not values:
        logger.warning("Sheet empty — creating headers and inserting rows")

        headers = [
            "job_link",
            "account_applied_by",
            "proposals",
            "last_viewed_by_client",
            "interviewing",
            "invite_sent",
            "unanswered_invites",
            "hires",
            "is_active",
            "is_viewed_by_client",
            "is_messaged",
            "applied_url",
            "created_at",
            "updated_at",
        ]

        rows = []
        for r in records:
            r_norm = {normalize_header(k): v for k, v in r.items()}
            r_norm["created_at"] = now_str
            r_norm["updated_at"] = now_str
            rows.append([r_norm.get(h, "") for h in headers])

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="RAW",
            body={"values": [headers] + rows},
        ).execute()
        return

    # Prepare DataFrame
    df = parse_sheet_to_df(values)
    headers = list(df.columns)

    if key_column_norm not in headers:
        raise ValueError(f"Key column '{key_column}' not found in sheet")
    
    if "created_at" not in headers or "updated_at" not in headers:
        raise ValueError("Sheet must contain 'created_at' and 'updated_at' columns")

    # Map existing rows by key
    key_to_row_index = {
        str(df.iloc[i][key_column_norm]): i + 2
        for i in range(len(df))
    }

    updates, appends = [], []

    for record in records:
        record_norm = {normalize_header(k): v for k, v in record.items()}
        key_value = str(record_norm.get(key_column_norm, ""))

        row_values = []
        for col in headers:
            if col == "created_at":
                if key_value in key_to_row_index:
                    # keep original
                    row_idx = key_to_row_index[key_value] - 2
                    row_values.append(df.iloc[row_idx]["created_at"])
                else:
                    row_values.append(now_str)

            elif col == "updated_at":
                row_values.append(now_str)

            else:
                row_values.append(record_norm.get(col, ""))

        if key_value in key_to_row_index:
            row_number = key_to_row_index[key_value]
            updates.append({
                "range": f"{sheet_name}!A{row_number}",
                "values": [row_values],
            })
        else:
            appends.append(row_values)

    try:
        # Batch updates
        if updates:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "valueInputOption": "RAW",
                    "data": updates,
                },
            ).execute()
            logger.info(f"Updated {len(updates)} rows")

        # Batch appends
        if appends:
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": appends},
            ).execute()
            logger.info(f"Appended {len(appends)} rows")

    except HttpError:
        logger.exception("Failed bulk upsert to sheet")
        raise


if __name__ == '__main__':
    # import json
    import os

    from dotenv import load_dotenv

    load_dotenv()
    
    SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    RANGE_NAME = 'user config!A1:H10'
    SHEET_NAME = "upwork_jobs"

    service = get_google_sheets_service()
    # Example of reading data
    # data = get_sheet_data(SPREADSHEET_ID, RANGE_NAME)
    # Example of appending jobs
    # BASE_PATH = Path(__file__).resolve().parent.parent
    # SAMPLE_JOBS_FILE = BASE_PATH / "scraped_data.json"

    # with open(SAMPLE_JOBS_FILE, 'r') as f:
    #     jobs_data = json.load(f)
    
    # data = batch_append_jobs(SPREADSHEET_ID, SHEET_NAME, jobs_data)

    # job_link_1 = "https://www.upwork.com/jobs/Phone-Number-Lists_~022010921100198862684/?referrer_url_path=/nx/search/jobs/"
    # update_1 = {
    #     "activity_data": "{}",
    #     "client_data": "{}",
    # }
    # job_link_2 = "https://www.upwork.com/jobs/Phone-Number-Lists_~022010921100198862684/?referrer_url_path=/nx/search/jobs/"
    # update_2 = {
    #     "filter_by": "filter_2 - max proposal exceeded",
    #     "filter_reason": "Max Proposals: 50 exceeds or equal to allowed max proposals: 50",
    #     "status": "skipped"
    # }
    # updates = [
    #     {
    #         "key": job_link_1,
    #         "values": update_1
    #     },
    #     {
    #         "key": job_link_2,
    #         "values": update_2
    #     }
    # ]
    # # # data = update_row_by_key(SPREADSHEET_ID, SHEET_NAME, "job_link", job_link_1, update_1)
    # data = batch_update_by_key(SPREADSHEET_ID, SHEET_NAME, updates)
    # if data:
    filters = {"status": "applied"}
    data = filter_sheet_data(SPREADSHEET_ID, SHEET_NAME, filters)
    print(data)
