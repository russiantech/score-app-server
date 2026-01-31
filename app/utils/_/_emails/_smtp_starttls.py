
from .base import *

async def _smtp_send_starttls(
    msg: EmailMessage,
):
    await aiosmtplib.send(
        msg,
        hostname=app_config.mail_config.smtp_host,
        port=587,
        username=app_config.mail_config.smtp_username,
        password=app_config.mail_config.smtp_password.strip(),
        start_tls=True,
        timeout=15,
    )

