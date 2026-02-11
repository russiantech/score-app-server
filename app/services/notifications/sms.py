import logging

logger = logging.getLogger(__name__)


async def send_verification_sms(phone: str, code: str) -> bool:
    try:
        logger.info(" Sending SMS to %s", phone)

        # await sms_provider.send(phone, f"Your code: {code}")

        return False  # Placeholder
    except Exception:
        logger.exception(" SMS sending failed")
        return False
