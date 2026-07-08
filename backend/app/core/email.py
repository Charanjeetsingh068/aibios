import asyncio
import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD and settings.SMTP_FROM_EMAIL)


def _send_sync(to: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, [to], msg.as_string())


async def send_email(to: str, subject: str, body: str) -> bool:
    """Sends a real transactional email over SMTP. Returns True only if the message was
    actually handed off to the SMTP server — never fakes success. Returns False (without
    raising) if SMTP isn't configured or the send fails, so callers can degrade gracefully
    (e.g. still log a dev-only fallback) rather than crash the request."""
    if not _smtp_configured():
        logger.warning(f"SMTP is not configured; skipping email to {to} (subject: {subject!r}).")
        return False
    try:
        await asyncio.to_thread(_send_sync, to, subject, body)
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False
