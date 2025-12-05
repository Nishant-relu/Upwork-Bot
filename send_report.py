import json
import logging
from datetime import datetime, timedelta

from config import configure_logging, paths
from utils import Email, get_env


configure_logging()
logger = logging.getLogger(__name__)


# smtp
smtp_server = get_env("SMTP_SERVER")
smtp_password = get_env("SMTP_PASSWORD")
smtp_user = get_env("SMTP_USER")
smtp_port = get_env("SMTP_PORT")
sender_email = get_env("SENDER_EMAIL")
sender_name = get_env("SENDER_NAME")
recepient_email = get_env("RECEPIENT_EMAIL")


def get_failed_jobs():
    try:
        previous_day = datetime.now().date() - timedelta(days=1)
        previous_day = previous_day.strftime("%Y-%m-%d")

        with open(paths.FAILED_JOB_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        failed_jobs_today = []
        current_date = None

        for line in lines:
            line:str = line.strip()
            if line[:10].count('-') == 2:
                current_date = line.split("|")[0].split(" ")[0].strip()
            if current_date == previous_day:
                failed_jobs_today.append(line)
        
        return failed_jobs_today
    except Exception as e:
        logger.error(f"Got an error in get_daily_report function: {e}", exc_info=True)


def get_daily_report() -> dict[str, str|int] | None:
    try:
        previous_day = datetime.now().date() - timedelta(days=1)

        filtered_jobs_stats_file:str = f"filtered_jobs_stats_{previous_day}.json"
        jobs_applied_stats_file:str = f"jobs_applied_{previous_day}.json"
        
        # filtered_jobs_stats_file = "filtered_jobs_stats_2025-10-13.json"
        # jobs_applied_stats_file = "jobs_applied_2025-10-13.json"

        with open(paths.APPLIED_JOBS_DIR/filtered_jobs_stats_file, 'r') as f:
            filtered_stats:dict[str, int] = json.load(f)

        with open(paths.APPLIED_JOBS_DIR/jobs_applied_stats_file, 'r') as f:
            jobs_applied_stats:dict[str, dict[str, int|list]] = json.load(f)

        logger.info(f"filtered jobs stats: {filtered_stats}") 
        logger.info(f"applied jobs stats: {jobs_applied_stats}")

        data:dict[str, str|int] = {}
        data["report_date"] = previous_day

        data.update(filtered_stats)

        total_job_applied = 0
        for key, value in jobs_applied_stats.items():
            jobs_applied = value.get("jobs_applied")
            data[key] = jobs_applied
            total_job_applied += jobs_applied
            data[f'invitation_by_{key}'] = value.get("invitation_applied")
        
        error_jobs = filtered_stats.get("total_jobs_after_filter_2", 0) - total_job_applied
        data["error_jobs"] = error_jobs

        logger.info(f"data: {data}" )
        
        return data
    
    except Exception as e:
        logger.error(f"Got an error in get_daily_report function: {e}", exc_info=True)


def send_daily_report():
    report_data = get_daily_report()

    html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document</title>
        </head>
        <body>
            <h2>Upwork Daily report is here:</h2> 

            <h4>Report Date: {report_data['report_date']}</h4>
            <h4>Total Unique Jobs Scraped: {report_data['unique_jobs']}</h4>
            <h4>Total Jobs Skipped by Filter 1: {report_data['skipped_filter1']['total']}</h4>
            <ul>
                <li>Less than min budget (300): {report_data['skipped_filter1']['cost']}</li>
                <li>Contains keyword [Lead Generation]: {report_data['skipped_filter1']['keyword']}</li>
            </ul>
            <h4>Total jobs after filter1: {report_data['total_jobs_after_filter_1']}</h4>
            <h4>Total Jobs Skipped by Filter 2: {report_data['skipped_filter2']['total']}</h4>
            <ul>
                <li>Activity and Client Data not found: {report_data['skipped_filter2']['no_activity_client_data']}</li>
                <li>Client Data not found: {report_data['skipped_filter2']['no_client_data']}</li>
                <li>Total Spent not found: {report_data['skipped_filter2']['total_spent']}</li>
                <li>Total Spent less than minimum total spent (5000): {report_data['skipped_filter2']['less_than_min_spent']}</li>
                <li>Client's Avg. hourly rate not found: {report_data['skipped_filter2']['hourly_rate']}</li>
                <li>Proposals info not found: {report_data['skipped_filter2']['proposal']}</li>
                <li>Proposal greater than max proposal (50): {report_data['skipped_filter2']['max_proposal']}</li>
                <li>Job in banned locations: {report_data['skipped_filter2'].get('location', 0)}</li>
            </ul>
            <h4>Total jobs after filter2: {report_data['total_jobs_after_filter_2']}</h4>
            <h4>Naman Account: </h4>
            <ul>
                <li><strong>Jobs applied: {report_data.get('naman', 0)}</strong></li>
                <li><strong>Invitation applied: {report_data.get('invitation_by_naman', 0)}</strong></li>
            </ul>
            <h4>Muktesh Account: </h4>
            <ul>
                <li><strong>Jobs applied: {report_data.get('muktesh', 0)}</strong></li>
                <li><strong>Invitation applied: {report_data.get('invitation_by_muktesh', 0)}</strong></li>
            </ul>
            <h4>Kishan Account: </h4>
            <ul>
                <li><strong>Jobs applied: {report_data.get('kishan', 0)}</strong></li>
                <li><strong>Invitation applied: {report_data.get('invitation_by_kishan', 0)}</strong></li>
            </ul>
            <h4>Error Jobs: {report_data.get('error_jobs', 0)}</h4>
            
        </body>
        </html>
    """
    try:

        subject = "Upwork report"

        # For testing
        # smtp_server = "smtp-mail.outlook.com"
        # smtp_password = "JaggaDaku<<162357>>"
        # smtp_user = "sushilvarma@reluconsultancy.in"
        # smtp_port = 587
        # sender_email = "sushilvarma@reluconsultancy.in"
        # sender_name = "Sushil varma"
        # recepient_email = "sushilvarma@reluconsultancy.in"

        # logger.info(f"smtp server: {smtp_server} \nsmtp port: {smtp_port} \nsmtp user: {smtp_user} \nsmtp password: {smtp_password}")

        email = Email(smtp_server, smtp_port, smtp_user, smtp_password)
        
        logger.info("Sending email...")
        email.send_email(subject, html_body, recepient_email, sender_email, sender_name, html=True)

        logger.info("Email sent successfully!")
    
    except Exception as e:
        logger.error(f"Got unexpected error while sending email: {e}", exc_info=True)

def send_faild_jobs():

    failed_jobs = get_failed_jobs()
    if failed_jobs:
        body = "Here are the failed job applications for today:\n\n" + "\n".join(failed_jobs)
    else:
        body = "No failed job applications recorded for today."
    
    try:

        subject = "Failed job stats"

        # For testing
        # smtp_server = "smtp-mail.outlook.com"
        # smtp_password = "JaggaDaku<<162357>>"
        # smtp_user = "sushilvarma@reluconsultancy.in"
        # smtp_port = 587
        # sender_email = "sushilvarma@reluconsultancy.in"
        # sender_name = "Sushil varma"
        recepient_email = "sushilvarma@reluconsultancy.in"

        # logger.info(f"smtp server: {smtp_server} \nsmtp port: {smtp_port} \nsmtp user: {smtp_user} \nsmtp password: {smtp_password}")

        email = Email(smtp_server, smtp_port, smtp_user, smtp_password)
        
        logger.info("Sending email...")
        email.send_email(subject, body, recepient_email, sender_email, sender_name)

        logger.info("Email sent successfully!")
    
    except Exception as e:
        logger.error(f"Got unexpected error while sending email: {e}", exc_info=True)


def main():
    send_daily_report()
    send_faild_jobs()


if __name__ == '__main__':
    # send_faild_jobs()
    main()
