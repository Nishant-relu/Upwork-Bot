import logging
from functools import lru_cache
from pathlib import Path

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "upwork-bot-service-account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


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


def get_google_sheets_service(
    service_account_file: Path | str | None = None,
) -> Resource:
    """
    Create and return a Google Sheets API service.
    """
    service_account_file = service_account_file or SERVICE_ACCOUNT_FILE

    try:
        creds = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=SCOPES,
        )
        return build("sheets", "v4", credentials=creds)
    except Exception as exc:
        logger.exception(f"Failed to create Google Sheets service. error: {exc}")
        raise


@lru_cache(maxsize=32)
def fetch_sheet_values(
    spreadsheet_id: str,
    range_name: str,
) -> list[list]:
    """
    Fetch raw values from Google Sheets.
    """
    service = get_google_sheets_service()

    try:
        result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueRenderOption="UNFORMATTED_VALUE",
            )
            .execute()
        )
        return result.get("values", [])
    except HttpError:
        logger.exception("Google Sheets API error")
        return []


def parse_sheet_to_df(values: list[list]) -> pd.DataFrame:
    """
    Convert raw sheet values to DataFrame.
    """
    if not values:
        return pd.DataFrame()

    headers = [normalize_header(h) for h in values[0]]
    rows = values[1:]

    return pd.DataFrame(rows, columns=headers).fillna("")


def get_sheet_data(
    spreadsheet_id: str,
    range_name: str,
) -> list[dict]:
    """
    Fetch Google Sheet data as list of dicts.
    """
    try:
        values = fetch_sheet_values(spreadsheet_id, range_name)
        df = parse_sheet_to_df(values)
        return df.to_dict(orient="records")
    except Exception:
        logger.exception("Failed to fetch sheet data")
        return []


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()
    
    SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    RANGE_NAME = 'user config!A1:H10'

    service = get_google_sheets_service()
    # Example of reading data
    data = get_sheet_data(SPREADSHEET_ID, RANGE_NAME)
    # if data:
    print(data)
