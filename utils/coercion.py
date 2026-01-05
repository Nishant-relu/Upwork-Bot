from typing import Any
from config.schema import ProposalType


def coerce_value(key: str, value: Any) -> Any:
    if value in ("", None):
        return None

    if key in {"min_budget", "min_total_spent", "max_proposal"}:
        return int(value)

    if key in {"wait_time", "retry_interval_minute"}:
        return tuple(int(v.strip()) for v in str(value).split(","))

    if key in {"skip_keywords", "skip_locations"}:
        return tuple(v.strip() for v in str(value).split(",") if v.strip())

    if key == "proposal_type":
        return ProposalType(value.lower())

    return value
