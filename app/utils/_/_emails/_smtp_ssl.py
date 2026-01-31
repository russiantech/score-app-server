from .base import *

async def _smtp_send_ssl(
    msg: EmailMessage,
):
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



