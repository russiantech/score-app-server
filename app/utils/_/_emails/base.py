
from email.message import EmailMessage
import logging
import aiosmtplib
from server.app.core.config import get_app_config

app_config = get_app_config()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure DEBUG messages are shown

__all__ = [app_config, logger, aiosmtplib, EmailMessage]