""" 
Delivery strategy logic 

"""

import logging
from email.message import EmailMessage

from .providers.smtp import send_starttls, send_ssl
from .providers.resend import send as send_resend
from .types import MailProvider

logger = logging.getLogger(__name__)


PROVIDERS = [
    (MailProvider.SMTP_STARTTLS, send_starttls),
    (MailProvider.SMTP_SSL, send_ssl),
    (MailProvider.RESEND_API, send_resend),
]


async def send_with_fallback(msg: EmailMessage) -> bool:
    for provider, sender in PROVIDERS:
        try:
            logger.info(f" Sending email via {provider}")
            await sender(msg)
            logger.info(f" Email sent via {provider}")
            return True
        except Exception as exc:
            logger.warning(
                f"️ {provider} failed: {exc.__class__.__name__}: {exc}"
            )

    logger.error(" All email providers failed")
    return False

