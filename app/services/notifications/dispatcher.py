
""" 
Core Dispatcher (Single Source of Truth)
"""

from fastapi import BackgroundTasks
from typing import Optional
from app.services.mail.service import send_email, send_email_background

from app.core.config import get_app_config
app_config = get_app_config()

async def dispatch_email(
    *,
    subject: str,
    to: str,
    html: str,
    text: str,
    background_tasks: Optional[BackgroundTasks] = None,
    critical: bool = False,
):
    """
    Unified email dispatcher.
    - critical=True  -> realtime (await)
    - critical=False -> background (fire & forget)
    """

    provider = app_config.mail_config.provider

    if critical or not background_tasks:
        return await send_email(
            subject=subject,
            to=to,
            html_body=html,
            text_body=text,
            # via=provider,
        )

    send_email_background(
        subject=subject,
        to=to,
        html_body=html,
        text_body=text,
        background_tasks=background_tasks,
        # via=provider,
    )

