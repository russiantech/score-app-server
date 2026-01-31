# RESEND Provider

""" 
✔ Clean
✔ Replaceable
"""
import resend
from email.message import EmailMessage
from app.core.config import get_app_config

app_config = get_app_config()


async def send(msg: EmailMessage) -> None:
    resend.api_key = app_config.mail_config.resend_api_key

    resend.Emails.send({
        "from": f"{app_config.mail_config.mail_sender_name} <{app_config.mail_config.mail_sender_email}>",
        "to": msg["To"].split(", "),
        "subject": msg["Subject"],
        "html": msg.get_body(preferencelist=("html",)).get_content(),
        "text": msg.get_body(preferencelist=("plain",)).get_content(),
    })
