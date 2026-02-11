# SMTP Providers

""" 
 No logging
 No fallback logic
 Pure transport layer
"""

import aiosmtplib
from email.message import EmailMessage
from app.core.config import get_app_config

app_config = get_app_config()


async def send_starttls(msg: EmailMessage) -> None:
    await aiosmtplib.send(
        msg,
        hostname=app_config.mail_config.smtp_host,
        port=587,
        username=app_config.mail_config.smtp_username,
        password=app_config.mail_config.smtp_password.strip(),
        start_tls=True,
        timeout=15,
    )


async def send_ssl(msg: EmailMessage) -> None:
    await aiosmtplib.send(
        msg,
        hostname=app_config.mail_config.smtp_host,
        port=465,
        username=app_config.mail_config.smtp_username,
        password=app_config.mail_config.smtp_password.strip(),
        use_tls=True,
        start_tls=False,
        timeout=15,
    )

