import logging
from dataclasses import dataclass, field
from typing import Any, Tuple

from config.schema import ProposalType, UserConfig
from services.google_service import get_sheet_data
from utils.coercion import coerce_value
from utils.env import get_env

logger = logging.getLogger(__name__)

SPREADSHEET_ID = get_env("GOOGLE_SHEETS_SPREADSHEET_ID")


@dataclass(frozen=True)
class Settings:
    MAX_RETRY: int = 5
    RETRY_INTERVAL_MINUTE: Tuple[int, int] = (2, 5)

    MIN_BUDGET: int = 300
    MIN_TOTAL_SPENT: int = 5000
    MAX_PROPOSAL: int = 50

    SKIP_KEYWORDS: Tuple[str, ...] = ("Lead Generation",)
    SKIP_LOCATIONS: Tuple[str, ...] = (
        "Pakistan",
        "Bangladesh",
        "Sri Lanka",
        "Nepal",
        "Bhutan",
    )

    WAIT_TIME: Tuple[int, int] = (20, 30)

    PROPOSAL_TYPE: ProposalType = ProposalType.FREELANCER
    USER_CONFIG: dict[str, UserConfig] = field(default_factory=dict)

    PROXY_HOST: str = get_env("PROXY_HOST")
    PROXY_PORT: str = get_env("PROXY_PORT")
    PROXY_USER: str = get_env("PROXY_USER")
    PROXY_PASSWORD: str = get_env("PROXY_PASSWORD")

    def get_worker_user(self) -> UserConfig:
        workers = [u for u in self.USER_CONFIG.values() if u.account_type == "worker"]
        if not workers:
            raise ValueError("No worker user found in USER_CONFIG")
        if len(workers) > 1:
            raise ValueError("Multiple worker users found in USER_CONFIG")
        return workers[0]


def load_settings_from_sheet(
    spreadsheet_id: str,
    range_name: str,
) -> dict[str, Any]:
    rows = get_sheet_data(spreadsheet_id, range_name)

    config: dict[str, Any] = {}

    for row in rows:
        key = row.get("key")
        value = row.get("value")

        if not key:
            continue

        try:
            config[key.upper()] = coerce_value(key.lower(), value)
        except Exception:
            logger.exception("Invalid config value: %s=%s", key, value)
            raise

    return config


def load_user_config(
    spreadsheet_id: str,
    range_name: str,
) -> dict[str, UserConfig]:
    """Load user configurations from Google Sheets."""

    rows = get_sheet_data(spreadsheet_id, range_name)

    users: dict[str, UserConfig] = {}

    for row in rows:
        name = row.get("name")
        if not name:
            continue

        try:
            user = UserConfig(
                name=name.lower(),
                email=row["email"],
                password=row["password"],
                security_answer=row["security_answer"],
                account_type=row["account_type"].lower(),
                hourly_rate=float(row.get("hourly_rate") or 0),
                min_client_hourly_rate=float(row.get("min_client_hourly_rate") or 0),
                max_client_hourly_rate=float(row.get("max_client_hourly_rate") or 0),
            )
            users[user.name] = user

        except Exception:
            logger.exception("Invalid user row: %s", row)
            raise

    return users


def validate_user_configs(users: dict[str, UserConfig]) -> None:
    applicants = [u for u in users.values() if u.account_type == "applicant"]

    for user in applicants:
        if user.min_client_hourly_rate > user.max_client_hourly_rate:
            raise ValueError(
                f"Invalid rate range for {user.name}: "
                f"{user.min_client_hourly_rate} > {user.max_client_hourly_rate}"
            )

    # Check overlapping ranges
    ranges = sorted(
        (
            (u.min_client_hourly_rate, u.max_client_hourly_rate, u.name)
            for u in applicants
        ),
        key=lambda x: x[0],
    )

    for i in range(len(ranges) - 1):
        _, max_r, name = ranges[i]
        next_min, _, next_name = ranges[i + 1]

        if max_r > next_min:
            raise ValueError(f"Overlapping rate ranges: {name} ↔ {next_name}")


def build_settings() -> Settings:
    sheet_config = load_settings_from_sheet(
        SPREADSHEET_ID,
        "Sheet3!A1:B50",
    )

    user_config = load_user_config(
        SPREADSHEET_ID,
        "user config!A1:H10",
    )

    validate_user_configs(user_config)

    return Settings(
        USER_CONFIG=user_config,
        **{k: v for k, v in sheet_config.items() if v is not None},
    )


bot_settings = build_settings()
