# Apply-to-review flow change plan

## Goal
Change the current pipeline so that after the first 3 filtering steps, the bot does not auto-apply to jobs anymore. Instead, it should send a notification email with the passed jobs so a human can apply manually.

## Current behavior
1. Read job notifications from Upwork.
2. Scrape the related jobs.
3. Run filter 1.
4. Run filter 2.
5. Run filter 3 (ML filter).
6. Categorize the jobs and auto-apply through the browser.

## New behavior
1. Read job notifications from Upwork.
2. Scrape the related jobs.
3. Run filter 1.
4. Run filter 2.
5. Run filter 3 (ML filter).
6. Send an email notification containing the filtered jobs for human review.
7. Stop there; no auto-apply step.

## Files likely to change
- main.py
  - Remove/replace the final auto-apply flow.
  - Add a step that prepares and sends a notification for the passed jobs.

- main_2.py
  - This is the main active flow for the bot.
  - Replace the final apply phase with an email-notification phase.

- utils/email_service.py
  - Reuse this SMTP helper for sending review emails.

- utils/job_notification_service.py
  - Create this helper if you want the email body formatting to be separated from the main bot logic.

- config/constants.py
  - Optional: add notification-related config values if needed.

- .env or environment settings
  - Add SMTP and recipient values for the review email.

## Suggested implementation steps
1. Keep the notification, scraping, and filtering logic unchanged.
2. Remove the browser-based apply section from the final stage.
3. Add a new notification step after the ML filter passes jobs.
4. Build the email body from the passed jobs.
5. Send the email using the existing SMTP utility.
6. Update logs/status handling so the jobs are marked as "ready_for_review" instead of "applied".

## Notes
- This change is mostly about replacing the last step, not rewriting the earlier pipeline.
- The first 3 stages can stay as they are.
- The main work is to swap the final "apply" action with a "notify human" action.
