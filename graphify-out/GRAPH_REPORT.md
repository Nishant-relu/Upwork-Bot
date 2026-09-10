# Graph Report - upwork_bot  (2026-09-09)

## Corpus Check
- 66 files · ~22,864 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 493 nodes · 1033 edges · 33 communities (28 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `451659ad`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- track_job_activity.py
- JobFilter
- utils/__init__.py
- UpworkJobApplication
- collect_activity_records
- google_service.py
- selectors/__init__.py
- Page
- datetime
- .scrape_jobs
- UserConfig
- UpworkLoginManager
- BeautifulSoup
- deploy.sh
- Filter1
- bot_scheduler.py
- filter_stats.py
- save_url
- main_2.py
- JobHtmlParser
- main.py
- job_stats.py
- PathConfig
- .__init__
- filter.py
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
- `main()` --indirect_call--> `get_sheet_gid()`  [INFERRED]
  main_2.py → services/google_service.py
- `main()` --uses--> `ContextHandler`  [INFERRED]
  upwork/apply.py → browser/context.py
- `main()` --uses--> `ContextHandler`  [INFERRED]
  upwork/auth.py → browser/context.py
- `attempt_job_application()` --uses--> `UserConfig`  [INFERRED]
  main.py → config/schema.py
- `scrape_and_filter_jobs()` --uses--> `UserConfig`  [INFERRED]
  main.py → config/schema.py

## Import Cycles
- None detected.

## Communities (33 total, 5 thin omitted)

### Community 0 - "track_job_activity.py"
Cohesion: 0.07
Nodes (34): Browser, AntiCloudflare, Moves mouse from (x1, y1) to (x2, y2) using sinusoidal easing, main(), PatchrightBrowser, get_proxy_ip(), Page, Validates whether the current IP matches the expected proxy IP. (+26 more)

### Community 1 - "JobFilter"
Cohesion: 0.23
Nodes (7): JobFilter, Apply initial filtering rules: duplicates, low budget, keywords., Handles filtering logic for Upwork job listings based on predefined rules, Apply both filters on a job entry., Validate or login using cookies., Apply filtering on a list of job data., Check whether a job URL has already been processed.

### Community 2 - "utils/__init__.py"
Cohesion: 0.07
Nodes (31): get_daily_report(), get_failed_jobs(), main(), send_daily_report(), send_faild_jobs(), get_credentials(), gets login credentials from env based on name of user., download_file() (+23 more)

### Community 3 - "UpworkJobApplication"
Cohesion: 0.07
Nodes (23): main(), Page, Extract job title, description, and custom questions from the HTML source., Extract job details from the current page., Fill out the cover letter on the job application form., Check if dropdown has the expected selected value., Automates the process of applying for jobs on Upwork using a Selenium-based…, Accept the "Understand and Agree" consent form if present. (+15 more)

### Community 4 - "collect_activity_records"
Cohesion: 0.29
Nodes (10): collect_activity_records(), determine_job_active_status(), extract_job_activity(), open_page_with_retry(), Any, Page, Navigate to a URL with retry + captcha handling. Returns True if page…, Extract activity metrics from job details page. (+2 more)

### Community 5 - "google_service.py"
Cohesion: 0.11
Nodes (38): Any, DataFrame, Path, Resource, batch_append_jobs(), _batch_update(), batch_update_by_key(), build_row_index_by_column() (+30 more)

### Community 6 - "selectors/__init__.py"
Cohesion: 0.08
Nodes (21): ActivityParser, Extracts activity stats from job HTML., ClientInfoParser, Extracts client info from job HTML., JobCardParser, Tag, Parses a single job card from the job listings page., find_element() (+13 more)

### Community 8 - "datetime"
Cohesion: 0.13
Nodes (25): clean_dated_json_files(), clean_log_folders(), clean_screenshot_files(), date_from_filename(), is_old(), main(), mtime(), Path (+17 more)

### Community 9 - ".scrape_jobs"
Cohesion: 0.25
Nodes (5): Tag, Save scraped data to a JSON file., Scrape job listings from the given URL or default Upwork job URL., Path, save_scraped_jobs()

### Community 10 - "UserConfig"
Cohesion: 0.22
Nodes (15): ProposalType, Enum, UserConfig, build_settings(), load_settings_from_sheet(), load_user_config_from_sheet(), Any, Load user configurations from Google Sheets. (+7 more)

### Community 11 - "UpworkLoginManager"
Cohesion: 0.17
Nodes (11): main(), Page, Standard Login Procedure, Validate login using session or fallback to credentials., Manages the login process for Upwork, Initialize with a Patchright., Handles Upwork security question if prompted., Validates if login was successful by checking for jobs feed. (+3 more)

### Community 12 - "BeautifulSoup"
Cohesion: 0.09
Nodes (16): BeautifulSoup, fetch_history_job(), Open a history job's own page in `history_page` (a second tab) and return its…, AttachmentParser, extracts all the attachments, ClientHistoryParser, Proposals come as a range ("5 to 10", "Less than 5", "50+") -> {min, max};…, Activity on this job" data off a history job's own page. (+8 more)

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
Cohesion: 0.07
Nodes (41): apply_filter_1(), apply_filter_2(), assign_accounts(), collect_all_notifications(), deduplicate_jobs(), expand_client_history(), extract_job_id_from_url(), fetch_notifications() (+33 more)

### Community 23 - "JobHtmlParser"
Cohesion: 0.27
Nodes (5): Filter based on client data fields., Second layer of filtering using job detail page content., JobHtmlParser, Save a job URL and optional reason for skipping to the file., save_url()

### Community 24 - "main.py"
Cohesion: 0.17
Nodes (17): attempt_job_application(), categorize_jobs(), extract_job_id(), main(), ml_filter_jobs(), process_jobs_for_user(), Applies to a list of jobs for a given user., Third filtering layer using the ML prediction API. Only jobs with probability… (+9 more)

### Community 25 - "job_stats.py"
Cohesion: 0.32
Nodes (7): deduplicate_scraped_jobs(), merge_counters(), Deduplicate scraped jobs based on job link., Save scraped jobs data to Google Sheets, Recursively merge two dicts d1 and d2 that have the same structure. Wherever…, save_job_filter_stats(), save_jobs_to_sheet()

### Community 26 - "PathConfig"
Cohesion: 0.38
Nodes (4): PathConfig, Ensure all required directories exist., Configuration class for managing project directory paths., Ensure essential files exist.

### Community 29 - ".__init__"
Cohesion: 0.50
Nodes (3): Page, Path, Initialize with a SeleniumBase browser instance.

### Community 31 - "filter.py"
Cohesion: 0.18
Nodes (9): ContextHandler, Path, Scrape and filter jobs from Upwork using the default or given user., scrape_and_filter_jobs(), main(), JobScraper, Page, A scraper class to extract job listings from Upwork. (+1 more)

## Knowledge Gaps
- **2 isolated node(s):** `DISPLAY`, `graphify`
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UpworkJobApplication` connect `UpworkJobApplication` to `main.py`, `track_job_activity.py`, `UserConfig`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `UpworkLoginManager` connect `UpworkLoginManager` to `track_job_activity.py`, `JobFilter`, `UpworkJobApplication`, `google_service.py`, `UserConfig`, `main_2.py`, `main.py`, `filter.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `handle_captcha()` connect `track_job_activity.py` to `UpworkJobApplication`, `collect_activity_records`, `UpworkLoginManager`, `main_2.py`, `filter.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `UpworkJobApplication` (e.g. with `attempt_job_application()` and `UserConfig`) actually correct?**
  _`UpworkJobApplication` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `UpworkLoginManager` (e.g. with `main()` and `UserConfig`) actually correct?**
  _`UpworkLoginManager` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ContextHandler` (e.g. with `main()` and `main()`) actually correct?**
  _`ContextHandler` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `UserConfig` (e.g. with `Settings` and `validate_user_configs()`) actually correct?**
  _`UserConfig` has 7 INFERRED edges - model-reasoned connections that need verification._