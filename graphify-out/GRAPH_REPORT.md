# Graph Report - upwork_bot  (2026-09-09)

## Corpus Check
- 66 files · ~22,827 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 493 nodes · 1033 edges · 36 communities (30 shown, 6 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `79cb6c2e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- .filter_jobs
- utils/__init__.py
- .handle_bid_form
- collect_activity_records
- google_service.py
- selectors/__init__.py
- browser/utils.py
- datetime
- .scrape_jobs
- settings.py
- UpworkLoginManager
- BeautifulSoup
- deploy.sh
- Filter1
- bot_scheduler.py
- filter_stats.py
- save_url
- main_2.py
- save_url
- scrape_client_history_for_jobs
- scrape_job_page
- constants.py
- get_oauth_token
- proposals_parser.py
- .__init__
- .__init__
- .__init__
- CLAUDE.md
- Page
- Any
- Path

## God Nodes (most connected - your core abstractions)
1. `UpworkJobApplication` - 27 edges
2. `UpworkLoginManager` - 24 edges
3. `ContextHandler` - 19 edges
4. `UserConfig` - 19 edges
5. `handle_captcha()` - 19 edges
6. `JobFilter` - 17 edges
7. `dismiss_cookies_popup()` - 16 edges
8. `get_proxy()` - 16 edges
9. `JobHtmlParser` - 14 edges
10. `configure_logging()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `get_oauth_token()` --calls--> `get_proxy()`  [INFERRED]
  main_2.py → utils/proxy.py
- `scrape_new_jobs()` --calls--> `get_proxy()`  [INFERRED]
  main_2.py → utils/proxy.py
- `ml_filter_jobs()` --calls--> `format_prediction_score()`  [INFERRED]
  main_2.py → utils/ml_filter.py
- `ml_filter_jobs()` --indirect_call--> `predict_job()`  [INFERRED]
  main_2.py → utils/ml_filter.py
- `expand_client_history()` --uses--> `ClientHistoryParser`  [INFERRED]
  main_2.py → upwork/parsers/history_parser.py

## Import Cycles
- None detected.

## Communities (36 total, 6 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.07
Nodes (49): Browser, ContextHandler, Path, main(), dismiss_cookies_popup(), handle_captcha(), Dismiss the cookie consent popup on websites using OneTrust, if present., Handle Captcha if present (+41 more)

### Community 1 - ".filter_jobs"
Cohesion: 0.15
Nodes (8): Apply initial filtering rules: duplicates, low budget, keywords., Apply both filters on a job entry., Validate or login using cookies., Apply filtering on a list of job data., Check whether a job URL has already been processed., merge_counters(), Recursively merge two dicts d1 and d2 that have the same structure. Wherever…, save_job_filter_stats()

### Community 2 - "utils/__init__.py"
Cohesion: 0.06
Nodes (39): ml_filter_jobs(), Third filtering layer using the ML prediction API. Only jobs with probability…, get_daily_report(), get_failed_jobs(), main(), send_daily_report(), send_faild_jobs(), normalize_country() (+31 more)

### Community 3 - ".handle_bid_form"
Cohesion: 0.13
Nodes (9): Fill out the cover letter on the job application form., Check if dropdown has the expected selected value., Accept the "Understand and Agree" consent form if present., Fill out custom job questions with provided answers., Verify proposal submission, Fill and submit the hourly-rate-based job application form., Fill and submit bid based job application form, Fill and submit the milestone/project-based job application form. (+1 more)

### Community 4 - "collect_activity_records"
Cohesion: 0.19
Nodes (12): collect_activity_records(), determine_job_active_status(), extract_job_activity(), open_page_with_retry(), Any, Page, Navigate to a URL with retry + captcha handling. Returns True if page…, Extract activity metrics from job details page. (+4 more)

### Community 5 - "google_service.py"
Cohesion: 0.09
Nodes (44): Any, DataFrame, Path, Resource, batch_append_jobs(), _batch_update(), batch_update_by_key(), build_row_index_by_column() (+36 more)

### Community 6 - "selectors/__init__.py"
Cohesion: 0.11
Nodes (16): ClientInfoParser, JobCardParser, Tag, Parses a single job card from the job listings page., find_element(), format_price(), format_text(), Tag (+8 more)

### Community 7 - "browser/utils.py"
Cohesion: 0.09
Nodes (18): AntiCloudflare, Page, Moves mouse from (x1, y1) to (x2, y2) using sinusoidal easing, PatchrightBrowser, get_proxy_ip(), Page, Validates whether the current IP matches the expected proxy IP., Fetch the current public IP address as seen by the browser. (+10 more)

### Community 8 - "datetime"
Cohesion: 0.13
Nodes (25): clean_dated_json_files(), clean_log_folders(), clean_screenshot_files(), date_from_filename(), is_old(), main(), mtime(), Path (+17 more)

### Community 9 - ".scrape_jobs"
Cohesion: 0.25
Nodes (5): Tag, Save scraped data to a JSON file., Scrape job listings from the given URL or default Upwork job URL., Path, save_scraped_jobs()

### Community 10 - "settings.py"
Cohesion: 0.14
Nodes (16): PathConfig, Ensure all required directories exist., Configuration class for managing project directory paths., Ensure essential files exist., ProposalType, Enum, build_settings(), load_settings_from_sheet() (+8 more)

### Community 11 - "UpworkLoginManager"
Cohesion: 0.18
Nodes (10): Page, Standard Login Procedure, Validate login using session or fallback to credentials., Manages the login process for Upwork, Initialize with a Patchright., Handles Upwork security question if prompted., Validates if login was successful by checking for jobs feed., Check if session still active. (+2 more)

### Community 12 - "BeautifulSoup"
Cohesion: 0.18
Nodes (8): BeautifulSoup, ClientHistoryParser, Proposals come as a range ("5 to 10", "Less than 5", "50+") -> {min, max};…, Activity on this job" data off a history job's own page., Freelancer name + id off a history row's "To freelancer: <a>Name</a>" line.…, Rows out of the currently loaded "Client's recent history" panel, most- recent…, Parses the "Client's recent history" panel on a job detail page, and the…, title / description / skills only, for a history job we don't need the full…

### Community 13 - "deploy.sh"
Cohesion: 0.48
Nodes (6): DISPLAY, error(), info(), deploy.sh script, success(), warn()

### Community 14 - "Filter1"
Cohesion: 0.33
Nodes (4): Filter1, Path, Check whether a job URL has already been processed., Apply initial filtering rules: duplicates, low budget, keywords.

### Community 15 - "bot_scheduler.py"
Cohesion: 0.47
Nodes (5): is_bot_running(), main(), Check if the bot script is already running., Activate virtualenv and run bot script., run_bot_with_venv()

### Community 16 - "filter_stats.py"
Cohesion: 0.47
Nodes (4): Filter1Reason, Filter2Reason, FilterStatsTracker, Enum

### Community 17 - "save_url"
Cohesion: 0.50
Nodes (3): Path, Save a job URL and optional reason for skipping to the file., save_url()

### Community 18 - "main_2.py"
Cohesion: 0.18
Nodes (15): assign_accounts(), deduplicate_jobs(), extract_job_id_from_url(), get_existing_sheet_job_ids(), main(), ml_filter_jobs(), Extract job ID token from Upwork job URL e.g. '~02abc123'., Fetch all job_id values already in Google Sheet. Used at pipeline start to skip… (+7 more)

### Community 23 - "save_url"
Cohesion: 0.20
Nodes (10): apply_filter_1(), apply_filter_2(), filter_jobs(), Filter 1: budget < MIN_BUDGET, forbidden keywords. Dedup is already handled in…, Filter 2: client data checks — total spent, hourly rate field, banned location,…, Run Filter 1 and Filter 2 on scraped jobs. Queues sheet updates for filter…, Filter based on client data fields., Second layer of filtering using job detail page content. (+2 more)

### Community 24 - "scrape_client_history_for_jobs"
Cohesion: 0.24
Nodes (11): expand_client_history(), fetch_history_job(), _fetch_page(), _is_low_funnel(), Navigate to URL with retry and captcha handling. Returns True on success., Click "View more" on the client-history panel until `max_clicks` history rows…, Open a history job's own page in `history_page` (a second tab) and return its…, True if a past job shows zero client engagement: no interviews, no invites.… (+3 more)

### Community 25 - "scrape_job_page"
Cohesion: 0.18
Nodes (7): parse_job_detail_html(), Navigate to one job detail page and extract all fields needed for filtering and…, Parse job-specific fields from the job listing detail page HTML. Selectors…, scrape_job_page(), AttachmentParser, extracts all the attachments, Extracts client info from job HTML.

### Community 26 - "constants.py"
Cohesion: 0.22
Nodes (4): main(), Manually refresh cookies. python refresh_cookies.py # every account except the…, refresh(), InvitationParser

### Community 27 - "get_oauth_token"
Cohesion: 0.29
Nodes (7): collect_all_notifications(), fetch_notifications(), get_oauth_token(), Launch a fresh browser for one applicant, login, extract oauth2_global_js_token…, Paginate through notifications and collect job/new ones from the last 24h.…, Loop all applicant accounts, extract OAuth token via browser, fetch latest…, UserConfig

### Community 28 - "proposals_parser.py"
Cohesion: 0.38
Nodes (3): ProposalsParser, Extracts active proposals data from HTML., ProposalSelectors

### Community 29 - ".__init__"
Cohesion: 0.50
Nodes (3): Page, Path, Initialize with a SeleniumBase browser instance.

## Knowledge Gaps
- **2 isolated node(s):** `graphify`, `DISPLAY`
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UpworkJobApplication` connect `main.py` to `.handle_bid_form`, `.__init__`, `browser/utils.py`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `UpworkLoginManager` connect `UpworkLoginManager` to `main.py`, `.filter_jobs`, `google_service.py`, `main_2.py`, `scrape_client_history_for_jobs`, `get_oauth_token`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `handle_captcha()` connect `main.py` to `scrape_client_history_for_jobs`, `UpworkLoginManager`, `collect_activity_records`, `browser/utils.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `UpworkJobApplication` (e.g. with `attempt_job_application()` and `UserConfig`) actually correct?**
  _`UpworkJobApplication` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `UpworkLoginManager` (e.g. with `main()` and `UserConfig`) actually correct?**
  _`UpworkLoginManager` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ContextHandler` (e.g. with `main()` and `main()`) actually correct?**
  _`ContextHandler` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `UserConfig` (e.g. with `Settings` and `validate_user_configs()`) actually correct?**
  _`UserConfig` has 7 INFERRED edges - model-reasoned connections that need verification._