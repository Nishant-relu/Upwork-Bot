
UPWORK_BASE_URL:str = "https://www.upwork.com"
UPWORK_LOGIN_URL:str = f"{UPWORK_BASE_URL}/ab/account-security/login"
UPWORK_SIGNUP_URL:str = f"{UPWORK_BASE_URL}/nx/signup/"
UPWORK_JOBS_SEARCH_URL:str = f"{UPWORK_BASE_URL}/nx/search/jobs/?from_recent_search=true&per_page=20&q=scraping"
UPWORK_PROPOSALS_URL:str = f"{UPWORK_BASE_URL}/nx/proposals/"
UPWORK_DASHBOARD_URL:str = f"{UPWORK_BASE_URL}/nx/find-work/best-matches"
IP_CHECK_URL:str = "https://ip.smartproxy.com/ip"
# PROPOSAL_API_URL = "http://147.93.116.17:8000/generate-response"
# PROPOSAL_API_URL = "http://5.78.43.182:9000/generate-response-json"
PROPOSAL_API_URL = "https://proposal.reluconsultancy.in/api/generate-response-json"
ML_PREDICT_API_URL = "https://predict.reluconsultancy.in/predict"

# Accounts that scrape notifications but never apply.
# Their rate range is excluded from overlap validation.
NO_APPLY_ACCOUNTS: set[str] = {"kishan"}
# Redirect a no-apply account's matched jobs to another account.
APPLY_REDIRECT: dict[str, str] = {"kishan": "muktesh"}
