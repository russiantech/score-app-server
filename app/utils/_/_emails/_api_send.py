import resend
from .base import *

async def _api_send_async(
    msg: EmailMessage,
):
    resend.api_key = app_config.mail_config.resend_api_key

    resend.Emails.send({
        "from": f"{app_config.mail_config.mail_sender_name} <{app_config.mail_config.mail_sender_email}>",
        "to": msg["To"].split(", "),
        "subject": msg["Subject"],
        "html": msg.get_body(preferencelist=("html",)).get_content(),
        "text": msg.get_body(preferencelist=("plain",)).get_content(),
    })

