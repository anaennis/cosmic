import os
import smtplib
from email.message import EmailMessage

# Gmail by default; any SMTP server with SSL works
DEFAULT_SMTP_HOST = 'smtp.gmail.com'
DEFAULT_SMTP_PORT = 465


def email_settings_from_env():
    """Reads email settings from the environment, raising if any are missing."""
    settings = {
        'user': os.getenv('EMAIL_USER'),
        'password': os.getenv('EMAIL_APP_PASSWORD'),
        'to': os.getenv('EMAIL_TO'),
        'host': os.getenv('SMTP_HOST', DEFAULT_SMTP_HOST),
        'port': int(os.getenv('SMTP_PORT', DEFAULT_SMTP_PORT)),
    }
    missing = [name for name, key in (('EMAIL_USER', 'user'),
                                      ('EMAIL_APP_PASSWORD', 'password'),
                                      ('EMAIL_TO', 'to')) if not settings[key]]
    if missing:
        raise ValueError(f"Missing email settings: {', '.join(missing)}")
    return settings


def build_message(subject, html_body, text_body, sender, recipients):
    """Builds a multipart email with a plain-text fallback and an HTML version."""
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = recipients
    message.set_content(text_body)
    message.add_alternative(html_body, subtype='html')
    return message


def send_digest_email(subject, html_body, text_body, settings):
    """Sends the digest; EMAIL_TO may hold several comma-separated addresses."""
    message = build_message(subject, html_body, text_body, settings['user'], settings['to'])
    with smtplib.SMTP_SSL(settings['host'], settings['port'], timeout=30) as server:
        server.login(settings['user'], settings['password'])
        server.send_message(message)
