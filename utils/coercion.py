from typing import Any
from config.schema import ProposalType


def coerce_value(key: str, value: Any) -> Any:
    if key in {"skip_keywords", "skip_locations"}:
        if value in ("", None):
            return ()   # empty in sheet = disable the filter entirely
        return tuple(v.strip() for v in str(value).split(",") if v.strip())

    if value in ("", None):
        return None

    if key in {"min_budget", "min_total_spent", "max_proposal"}:
        return int(value)

    if key in {"wait_time", "retry_interval_minute"}:
        return tuple(int(v.strip()) for v in str(value).split(","))

    if key == "proposal_type":
        return ProposalType(value.lower())

    return value
