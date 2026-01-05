from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class UserConfig:
    name: str
    email: str
    password:str
    security_answer: str
    account_type: str
    hourly_rate: float
    min_client_hourly_rate: float
    max_client_hourly_rate: float


class ProposalType(str, Enum):
    FREELANCER = "freelancer"
    AGENCY = "agency"
