
import logging
from email.message import EmailMessage

from aiosmtplib import send

from config import settings

logger = logging.getLogger(__name__)


async def send_email(recipient: str, subject: str, body: str):
    message = EmailMessage()

    message["From"] = settings.SMTP_EMAIL
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        await send(
            message,
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD,
        )

        logger.info("Email successfully sent to %s", recipient)

    except Exception:
        logger.exception("Failed to send email to %s", recipient)
