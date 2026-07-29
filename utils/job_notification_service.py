"""Email notification for jobs that passed all filters, for manual human review."""

import logging
from datetime import datetime
from html import escape

from utils.email_service import Email
from utils.env import get_env

logger = logging.getLogger(__name__)


def _job_row(job: dict) -> str:
    link = escape(job.get("link", ""))
    return f"""
        <tr>
            <td>{escape(job.get("title", "Untitled"))}</td>
            <td><a href="{link}">{link}</a></td>
            <td><strong>{escape(job.get("assigned_to", "") or "unassigned")}</strong></td>
        </tr>
    """


def build_review_email_body(jobs: list[dict]) -> str:
    """Build the HTML body listing jobs ready for manual review."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Upwork — {len(jobs)} job(s) ready for review</h2>
        <p>Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
            <tr style="background:#f0f0f0;">
                <th>Job Title</th><th>Link</th><th>Apply From</th>
            </tr>
            {"".join(_job_row(job) for job in jobs)}
        </table>
        <p>These jobs passed all filters. Please apply manually from the listed account.</p>
    </body>
    </html>
    """


def send_jobs_for_review(jobs: list[dict]) -> bool:
    """Send the review email. Returns True if sent."""
    if not jobs:
        logger.info("No jobs to send for review.")
        return False

    recipient = get_env("RECEPIENT_EMAIL")
    if not recipient:
        logger.error("RECEPIENT_EMAIL not set — cannot send review email.")
        return False

    email = Email(
        get_env("SMTP_SERVER"),
        get_env("SMTP_PORT"),
        get_env("SMTP_USER"),
        get_env("SMTP_PASSWORD"),
    )
    email.send_email(
        subject=f"Upwork: {len(jobs)} job(s) ready for review",
        body=build_review_email_body(jobs),
        recipient_email=recipient,
        sender_email=get_env("SENDER_EMAIL"),
        sender_name=get_env("SENDER_NAME"),
        html=True,
    )
    logger.info(f"Review email sent to {recipient} with {len(jobs)} job(s).")
    return True
