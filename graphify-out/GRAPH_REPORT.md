# Graph Report - upwork_bot  (2026-09-09)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 461 nodes · 1001 edges · 23 communities (22 shown, 1 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 35 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `38f50505`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main_2.py
- main.py
- utils/__init__.py
- UpworkJobApplication
- scrape_job_page
- google_service.py
- selectors/__init__.py
- handle_captcha
- datetime
- JobScraper
- UserConfig
- .check_session_persistence
- PathConfig
- deploy.sh
- Filter1
- bot_scheduler.py
- filter_stats.py
- save_url
- .__init__

## God Nodes (most connected - your core abstractions)
1. `UpworkJobApplication` - 27 edges
2. `UpworkLoginManager` - 24 edges
3. `UserConfig` - 21 edges
4. `ContextHandler` - 20 edges
5. `handle_captcha()` - 20 edges
6. `JobFilter` - 17 edges
7. `dismiss_cookies_popup()` - 17 edges
8. `JobHtmlParser` - 16 edges
9. `get_proxy()` - 16 edges
10. `configure_logging()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `UpworkLoginManager` --uses--> `UserConfig`  [INFERRED]
  upwork/auth.py → config/schema.py
- `scrape_job_page()` --uses--> `JobHtmlParser`  [INFERRED]
  main_2.py → upwork/parser.py
- `extract_job_activity()` --uses--> `JobHtmlParser`  [INFERRED]
  track_job_activity.py → upwork/parser.py
- `extract_job_activity()` --uses--> `UpworkJobDetailSelectors`  [INFERRED]
  track_job_activity.py → upwork/selectors/jobs_details_selectors.py
- `JobFilter` --uses--> `UserConfig`  [INFERRED]
  upwork/filter.py → config/schema.py

## Import Cycles
- None detected.

## Communities (23 total, 1 thin omitted)

### Community 0 - "main_2.py"
Cohesion: 0.07
Nodes (48): Browser, ContextHandler, Path, main(), dismiss_cookies_popup(), Dismiss the cookie consent popup on websites using OneTrust, if present., configure_logging(), ist_time_converter() (+40 more)

### Community 1 - "main.py"
Cohesion: 0.06
Nodes (45): ml_filter_jobs(), ML prediction filter — only jobs with probability >= 70% pass., attempt_job_application(), categorize_jobs(), extract_job_id(), main(), ml_filter_jobs(), process_jobs_for_user() (+37 more)

### Community 2 - "utils/__init__.py"
Cohesion: 0.08
Nodes (31): get_daily_report(), get_failed_jobs(), main(), send_daily_report(), send_faild_jobs(), normalize_country(), Normalize country name., get_credentials() (+23 more)

### Community 3 - "UpworkJobApplication"
Cohesion: 0.08
Nodes (21): Page, Extract job details from the current page., Fill out the cover letter on the job application form., Check if dropdown has the expected selected value., Automates the process of applying for jobs on Upwork using a Selenium-based…, Accept the "Understand and Agree" consent form if present., Initialize with a SeleniumBase browser instance., Selects the proposal type (Freelancer or Agency). (+13 more)

### Community 4 - "scrape_job_page"
Cohesion: 0.07
Nodes (26): BeautifulSoup, _fetch_page(), parse_job_detail_html(), Page, Navigate to URL with retry and captcha handling. Returns True on success., Navigate to one job detail page and extract all fields needed for filtering and…, Parse job-specific fields from the job listing detail page HTML. Selectors…, scrape_job_page() (+18 more)

### Community 5 - "google_service.py"
Cohesion: 0.13
Nodes (34): DataFrame, Resource, batch_append_jobs(), _batch_update(), batch_update_by_key(), build_row_index_by_column(), bulk_upsert_sheet_data(), execute_with_retry() (+26 more)

### Community 6 - "selectors/__init__.py"
Cohesion: 0.11
Nodes (17): ActivityParser, AttachmentParser, ClientInfoParser, InvitationParser, JobCardParser, Tag, Parses a single job card from the job listings page., ProposalsParser (+9 more)

### Community 7 - "handle_captcha"
Cohesion: 0.11
Nodes (18): AntiCloudflare, Page, Moves mouse from (x1, y1) to (x2, y2) using sinusoidal easing, PatchrightBrowser, get_proxy_ip(), Page, Validates whether the current IP matches the expected proxy IP., Fetch the current public IP address as seen by the browser. (+10 more)

### Community 8 - "datetime"
Cohesion: 0.13
Nodes (25): clean_dated_json_files(), clean_log_folders(), clean_screenshot_files(), date_from_filename(), is_old(), main(), mtime(), Path (+17 more)

### Community 9 - "JobScraper"
Cohesion: 0.12
Nodes (13): Tag, JobScraper, main(), Page, A scraper class to extract job listings from Upwork., Initialize with a SeleniumBase browser instance., Save scraped data to a JSON file., Fetch HTML page source from the given URL with retry logic. (+5 more)

### Community 10 - "UserConfig"
Cohesion: 0.24
Nodes (13): ProposalType, Enum, UserConfig, build_settings(), load_settings_from_sheet(), load_user_config_from_sheet(), Any, Load user configurations from Google Sheets. (+5 more)

### Community 11 - ".check_session_persistence"
Cohesion: 0.22
Nodes (6): Standard Login Procedure, Validate login using session or fallback to credentials., Handles Upwork security question if prompted., Validates if login was successful by checking for jobs feed., Check if session still active., Full login flow with email, password, and optional security question.

### Community 12 - "PathConfig"
Cohesion: 0.38
Nodes (4): PathConfig, Ensure all required directories exist., Configuration class for managing project directory paths., Ensure essential files exist.

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

## Knowledge Gaps
- **1 isolated node(s):** `DISPLAY`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UpworkJobApplication` connect `UpworkJobApplication` to `main_2.py`, `main.py`, `UserConfig`, `scrape_job_page`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Why does `UserConfig` connect `UserConfig` to `main_2.py`, `main.py`, `UpworkJobApplication`, `.check_session_persistence`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `UpworkLoginManager` connect `main_2.py` to `.__init__`, `main.py`, `UserConfig`, `.check_session_persistence`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `UpworkJobApplication` (e.g. with `attempt_job_application()` and `UserConfig`) actually correct?**
  _`UpworkJobApplication` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `UpworkLoginManager` (e.g. with `main()` and `UserConfig`) actually correct?**
  _`UpworkLoginManager` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `UserConfig` (e.g. with `Settings` and `validate_user_configs()`) actually correct?**
  _`UserConfig` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ContextHandler` (e.g. with `main()` and `main()`) actually correct?**
  _`ContextHandler` has 3 INFERRED edges - model-reasoned connections that need verification._