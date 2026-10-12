"""Small SMTP mailer for Hire Cloud account emails."""
import smtplib
from email.message import EmailMessage

from flask import current_app


def send_account_email(recipient, subject, text_body):
    host = current_app.config.get("MAIL_SERVER")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER")
    if not host or not sender:
        current_app.logger.warning("Account email not sent: SMTP is not configured.")
        return False
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(text_body)
    port = int(current_app.config.get("MAIL_PORT", 587))
    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.ehlo()
        if current_app.config.get("MAIL_USE_TLS", True):
            smtp.starttls()
            smtp.ehlo()
        username = current_app.config.get("MAIL_USERNAME") or ""
        if username:
            smtp.login(username, current_app.config.get("MAIL_PASSWORD") or "")
        smtp.send_message(message)
    return True
