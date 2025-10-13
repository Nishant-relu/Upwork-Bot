import logging
from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import Tuple, Type
from utils.env import get_env


logger = logging.getLogger(__name__)


class ProposalType(str, Enum):
    FREELANCER = "freelancer"
    AGENCY = "agency"


class HourlyRate(IntEnum):
    KISHAN = 10
    NAMAN = 20
    MUKTESH = 30

    @classmethod
    def get_by_name(cls, name: str) -> int:
        """
        Returns the numeric hourly rate based on name (case-insensitive).
        Raises ValueError if name is invalid.
        """
        try:
            return cls[name.upper()].value
        except KeyError:
            raise ValueError(f"Invalid hourly rate name: {name}")


@dataclass(frozen=True)
class Settings:

    MAX_RETRY: int = 5
    RETRY_INTERVAL_MINUTE: Tuple[int, int] = (2, 5)

    MIN_BUDGET: int = 300
    MIN_TOTAL_SPENT: int = 5000
    MAX_PROPOSAL: int = 50
    SKIP_KEYWORDS: Tuple[str, ...] = ('Lead Generation',)
    # add Standard ISO country names only
    SKIP_LOCATIONS: Tuple[str, ...] = (
        'Pakistan',
        'Bangladesh',
        'Sri Lanka',
        'Nepal',
        'Bhutan',
    )

    WAIT_TIME: Tuple[int, int] = (20, 30)

    PROPOSAL_TYPE: ProposalType = ProposalType.FREELANCER
    HOURLY_RATE: Type[HourlyRate] = HourlyRate

    # Proxy configuration from environment
    PROXY_HOST: str = get_env("PROXY_HOST")
    PROXY_PORT: str = get_env("PROXY_PORT")
    PROXY_USER: str = get_env("PROXY_USER")
    PROXY_PASSWORD: str = get_env("PROXY_PASSWORD")


bot_settings = Settings()
