import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import logging
from app.config.settings import settings

class SmtpSender:
    def __init__(self, host: str, port: int, username: str, password: str, starttls: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.starttls = starttls

    def send(self, account: dict, to_email: str, subject: str, html: str, text: Optional[str] = None):
        msg = MIMEMultipart('alternative')
        msg['From'] = account['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        part1 = MIMEText(text or '', 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.starttls:
                    server.starttls()
                server.login(self.username, self.password)
                server.sendmail(account['email'], to_email, msg.as_string())
        except Exception as e:
            logging.error(f"SMTP send failed: {e}")
            raise
