
from app._emails._smtp_starttls import _smtp_send_starttls
from app._emails._smtp_ssl import _smtp_send_ssl
from app._emails._api_send import _api_send_async

from .base import *

async def _send_with_fallback(msg: EmailMessage) -> bool:
    strategies = [
        ("SMTP_STARTTLS", _smtp_send_starttls),
        ("SMTP_SSL", _smtp_send_ssl),
        ("EMAIL_API", _api_send_async),
    ]

    for name, sender in strategies:
        try:
            logger.info(f"📤 Attempting email via {name}")
            await sender(msg)
            logger.info(f"✅ Email sent via {name}")
            return True
        except Exception as e:
            logger.warning(
                f"⚠️ {name} failed: {e.__class__.__name__}: {e}"
            )

    logger.error("❌ All email delivery strategies failed")
    return False
