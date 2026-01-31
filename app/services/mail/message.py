""" 
Message builder 
2️⃣ message.py – Build Email Once (DRY)

"""

from email.message import EmailMessage
from app.core.config import get_app_config

app_config = get_app_config()


def build_message(
    *,
    subject: str,
    recipients: list[str],
    html_body: str = "",
    text_body: str = "",
) -> EmailMessage:
    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = f"{app_config.mail_config.mail_sender_name} <{app_config.mail_config.smtp_username}>"
    msg["To"] = ", ".join(recipients)

    msg.set_content(text_body or " ")

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    return msg

