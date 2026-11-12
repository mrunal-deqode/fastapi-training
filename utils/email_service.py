import os
import logging
from dotenv import load_dotenv
from email.message import EmailMessage
from aiosmtplib import send

load_dotenv()

logger = logging.getLogger(__name__)


async def send_email(recipient: str, subject: str, body: str):
    message = EmailMessage()

    message["From"] = os.getenv("SMTP_EMAIL")
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        await send(message, hostname=os.getenv("SMTP_SERVER"), port=int(os.getenv("SMTP_PORT", "587")), start_tls=True, username=os.getenv("SMTP_EMAIL"), password=os.getenv("SMTP_PASSWORD"))

        logger.info("Email Successfully sent to %s", recipient)
        print(f"Email Successfully sent to {recipient}")

    except Exception:
        logger.exception("Fail to send Email")
