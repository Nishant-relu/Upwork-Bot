import json
import logging
from enum import Enum
from config import paths

logger = logging.getLogger(__name__)


class Filter1Reason(Enum):
    COST = "cost"
    KEYWORD = "keyword"

class Filter2Reason(Enum):
    TOTAL_SPENT = "total_spent"
    LESS_THAN_MIN_SPENT = "less_than_min_spent"
    HOURLY_RATE = "hourly_rate"
    NO_ACTIVITY_CLIENT_DATA = "no_activity_client_data"
    NO_CLIENT = "no_client_data"
    PROPOSAL = "proposal"
    MAX_PROPOSAL = "max_proposal"

class FilterStatsTracker:

    def __init__(self):
        self.counters = {
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
                'max_proposal': 0
            },
            'total_jobs_after_filter_1':0,
            'total_jobs_after_filter_2':0
        }
    
    