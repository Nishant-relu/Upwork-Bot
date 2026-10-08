# Graph Report - upwork_bot  (2026-09-10)

## Corpus Check
- 66 files · ~22,900 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 493 nodes · 1033 edges · 34 communities (26 shown, 8 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f9ea93f5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- track_job_activity.py
- handle_captcha
- utils/__init__.py
- UpworkJobApplication
- collect_activity_records
- google_service.py
- selectors/__init__.py
- Page
- datetime
- scrape_client_history_for_jobs
- UserConfig
- UpworkLoginManager
- BeautifulSoup
- deploy.sh
- Filter1
- bot_scheduler.py
- filter_stats.py
- proposals_parser.py
- main_2.py
- filter_jobs
- main.py
- scrape_job_page
- invitation_parser.py
- .parse
- .__init__
- Path
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
- `main()` --uses--> `ContextHandler`  [INFERRED]
  upwork/apply.py → browser/context.py
- `main()` --uses--> `ContextHandler`  [INFERRED]
  upwork/auth.py → browser/context.py
- `JobFilter` --uses--> `UserConfig`  [INFERRED]
  upwork/filter.py → config/schema.py
- `attempt_job_application()` --uses--> `UserConfig`  [INFERRED]
  main.py → config/schema.py
- `scrape_and_filter_jobs()` --uses--> `UserConfig`  [INFERRED]
  main.py → config/schema.py

## Import Cycles
- None detected.

## Communities (34 total, 8 thin omitted)

### Community 0 - "track_job_activity.py"
Cohesion: 0.09
Nodes (21): Browser, main(), PatchrightBrowser, configure_logging(), ist_time_converter(), Configure the root logger with file and stream handlers., PathConfig, Ensure all required directories exist. (+13 more)

### Community 1 - "handle_captcha"
Cohesion: 0.10
Nodes (21): AntiCloudflare, Moves mouse from (x1, y1) to (x2, y2) using sinusoidal easing, get_proxy_ip(), Page, Validates whether the current IP matches the expected proxy IP., Fetch the current public IP address as seen by the browser., validate_proxy_ip(), _capture_sidebar_overlay_state() (+13 more)

### Community 2 - "utils/__init__.py"
Cohesion: 0.07
Nodes (33): get_daily_report(), get_failed_jobs(), main(), send_daily_report(), send_faild_jobs(), get_credentials(), gets login credentials from env based on name of user., download_file() (+25 more)

### Community 3 - "UpworkJobApplication"
Cohesion: 0.08
Nodes (22): main(), Page, Extract job title, description, and custom questions from the HTML source., Extract job details from the current page., Fill out the cover letter on the job application form., Check if dropdown has the expected selected value., Automates the process of applying for jobs on Upwork using a Selenium-based…, Accept the "Understand and Agree" consent form if present. (+14 more)

### Community 4 - "collect_activity_records"
Cohesion: 0.29
Nodes (10): collect_activity_records(), determine_job_active_status(), extract_job_activity(), open_page_with_retry(), Any, Page, Navigate to a URL with retry + captcha handling. Returns True if page…, Extract activity metrics from job details page. (+2 more)

### Community 5 - "google_service.py"
Cohesion: 0.09
Nodes (42): Any, DataFrame, Path, Resource, batch_append_jobs(), _batch_update(), batch_update_by_key(), build_row_index_by_column() (+34 more)

### Community 6 - "selectors/__init__.py"
Cohesion: 0.08
Nodes (21): ActivityParser, Extracts activity stats from job HTML., ClientInfoParser, Extracts client info from job HTML., JobCardParser, Tag, Parses a single job card from the job listings page., find_element() (+13 more)

### Community 8 - "datetime"
Cohesion: 0.13
Nodes (25): clean_dated_json_files(), clean_log_folders(), clean_screenshot_files(), date_from_filename(), is_old(), main(), mtime(), Path (+17 more)

### Community 9 - "scrape_client_history_for_jobs"
Cohesion: 0.24
Nodes (11): expand_client_history(), fetch_history_job(), _fetch_page(), _is_low_funnel(), Navigate to URL with retry and captcha handling. Returns True on success., Click "View more" on the client-history panel until `max_clicks` history rows…, Open a history job's own page in `history_page` (a second tab) and return its…, True if a past job shows zero client engagement: no interviews, no invites.… (+3 more)

### Community 10 - "UserConfig"
Cohesion: 0.22
Nodes (15): ProposalType, Enum, UserConfig, build_settings(), load_settings_from_sheet(), load_user_config_from_sheet(), Any, Load user configurations from Google Sheets. (+7 more)

### Community 11 - "UpworkLoginManager"
Cohesion: 0.17
Nodes (11): main(), Page, Standard Login Procedure, Validate login using session or fallback to credentials., Manages the login process for Upwork, Initialize with a Patchright., Handles Upwork security question if prompted., Validates if login was successful by checking for jobs feed. (+3 more)

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

### Community 17 - "proposals_parser.py"
Cohesion: 0.38
Nodes (3): ProposalsParser, Extracts active proposals data from HTML., ProposalSelectors

### Community 18 - "main_2.py"
Cohesion: 0.14
Nodes (20): assign_accounts(), collect_all_notifications(), deduplicate_jobs(), extract_job_id_from_url(), fetch_notifications(), get_existing_sheet_job_ids(), get_oauth_token(), main() (+12 more)

### Community 23 - "filter_jobs"
Cohesion: 0.33
Nodes (6): apply_filter_1(), apply_filter_2(), filter_jobs(), Filter 1: budget < MIN_BUDGET, forbidden keywords. Dedup is already handled in…, Filter 2: client data checks — total spent, hourly rate field, banned location,…, Run Filter 1 and Filter 2 on scraped jobs. Queues sheet updates for filter…

### Community 24 - "main.py"
Cohesion: 0.06
Nodes (45): ContextHandler, attempt_job_application(), categorize_jobs(), extract_job_id(), main(), ml_filter_jobs(), process_jobs_for_user(), Applies to a list of jobs for a given user. (+37 more)

### Community 25 - "scrape_job_page"
Cohesion: 0.50
Nodes (4): parse_job_detail_html(), Navigate to one job detail page and extract all fields needed for filtering and…, Parse job-specific fields from the job listing detail page HTML. Selectors…, scrape_job_page()

### Community 29 - ".__init__"
Cohesion: 0.50
Nodes (3): Page, Path, Initialize with a SeleniumBase browser instance.

## Knowledge Gaps
- **2 isolated node(s):** `DISPLAY`, `graphify`
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UpworkJobApplication` connect `UpworkJobApplication` to `main.py`, `track_job_activity.py`, `UserConfig`, `handle_captcha`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `UpworkLoginManager` connect `UpworkLoginManager` to `track_job_activity.py`, `UpworkJobApplication`, `google_service.py`, `scrape_client_history_for_jobs`, `UserConfig`, `main_2.py`, `main.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `handle_captcha()` connect `handle_captcha` to `track_job_activity.py`, `UpworkJobApplication`, `collect_activity_records`, `scrape_client_history_for_jobs`, `UpworkLoginManager`, `main.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `UpworkJobApplication` (e.g. with `attempt_job_application()` and `UserConfig`) actually correct?**
  _`UpworkJobApplication` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `UpworkLoginManager` (e.g. with `main()` and `UserConfig`) actually correct?**
  _`UpworkLoginManager` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ContextHandler` (e.g. with `main()` and `main()`) actually correct?**
  _`ContextHandler` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `UserConfig` (e.g. with `Settings` and `validate_user_configs()`) actually correct?**
  _`UserConfig` has 7 INFERRED edges - model-reasoned connections that need verification._