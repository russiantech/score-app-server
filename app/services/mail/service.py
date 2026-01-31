""" 
Public API (send_email) 
The ONLY Public API

✔ Extremely clean
✔ Impossible to misuse
✔ Stable API for years

"""


from fastapi import BackgroundTasks
from pydantic import EmailStr

from .message import build_message
from .fallback import send_with_fallback


async def send_email(
    *,
    subject: str,
    to: EmailStr | list[EmailStr],
    html_body: str = "",
    text_body: str = "",
) -> bool:
    recipients = [to] if isinstance(to, str) else list(to)

    msg = build_message(
        subject=subject,
        recipients=recipients,
        html_body=html_body,
        text_body=text_body,
    )

    return await send_with_fallback(msg)


def send_email_background(
    *,
    subject: str,
    to: EmailStr | list[EmailStr],
    html_body: str,
    text_body: str,
    background_tasks: BackgroundTasks,
):
    recipients = [to] if isinstance(to, str) else list(to)

    msg = build_message(
        subject=subject,
        recipients=recipients,
        html_body=html_body,
        text_body=text_body,
    )

    background_tasks.add_task(send_with_fallback, msg)


