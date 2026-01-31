# Shared types / enums

""" 
from enum import Enum


class MailProvider(str, Enum):
    SMTP_STARTTLS = "smtp_starttls"
    SMTP_SSL = "smtp_ssl"
    RESEND_API = "resend_api"

"""

from enum import Enum


class MailProvider(str, Enum):
    SMTP_STARTTLS = "smtp_starttls"
    SMTP_SSL = "smtp_ssl"
    RESEND_API = "resend_api"

