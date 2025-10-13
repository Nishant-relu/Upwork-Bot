import logging
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr


logger = logging.getLogger(__name__)


class Email:
    def __init__(self, smtp_server:str, smtp_port:int, smtp_user:str, smtp_password:str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        
    def send_email(
            self, 
            subject:str, 
            body:str, 
            recipient_email:str,
            sender_email:str, 
            sender_name:str,
            cc_emails:list[str]|None=None, 
            html:bool=False
        ):
        try:
            # Set up the MIME
            msg = MIMEMultipart()
            msg['From'] = formataddr((sender_name, sender_email))
            msg['To'] = recipient_email
            msg['Subject'] = Header(subject, 'utf-8')

            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)

            # Attach body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls() 
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

        except Exception as e:
            logger.error(f"Error occurred while sending email: {e}", exc_info=True)
