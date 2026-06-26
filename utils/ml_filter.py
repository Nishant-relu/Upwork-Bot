import logging

import requests

from config.constants import ML_PREDICT_API_URL

logger = logging.getLogger(__name__)

ML_APPLY_THRESHOLD = 0.55


def build_ml_payload(job: dict) -> dict:
    """Build the ML API request payload — 7 client-history signals only."""
    client_data: dict = job.get("client_data", {})

    def _float(val) -> float:
        try:
            return float(str(val).replace(",", "").replace("%", "").replace("$", "").strip())
        except (ValueError, TypeError):
            return 0.0

    return {
        "client_total_spent": _float(client_data.get("total spent", 0)),
        "client_hire_rate":   _float(client_data.get("hire rate", 0)),
        "client_jobs_posted": _float(client_data.get("jobs posted", 0)),
        "open_jobs":          _float(client_data.get("open job", 0)),
        "client_hires":       _float(client_data.get("hires", 0)),
        "active":             _float(client_data.get("active", 0)),
        "hourly_rate":        _float(client_data.get("hourly rate", 0)),
    }


def format_prediction_score(probability: float) -> str:
    """Convert a 0-1 probability float to a percentage string e.g. 0.87 → '87%'."""
    return f"{round(probability * 100)}%"


def predict_job(job: dict) -> dict | None:
    """
    Call the ML prediction API for a single job.
    Returns the full raw response dict on success, None on any failure.
    """
    try:
        payload = build_ml_payload(job)
        logger.info(f"ML API payload: {payload}")

        response = requests.post(ML_PREDICT_API_URL, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        logger.info(f"ML API response: {result}")
        return result

    except requests.exceptions.Timeout:
        logger.warning(f"ML API timed out for job: {job.get('link', '')}")
    except requests.exceptions.HTTPError as e:
        logger.warning(f"ML API HTTP error for job {job.get('link', '')}: {e}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"ML API request failed for job {job.get('link', '')}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error calling ML API for job {job.get('link', '')}: {e}", exc_info=True)

    return None
