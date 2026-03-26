"""Service layer for application-specific email operations.

Rather than dealing with low-level SMTP details, other parts of the
codebase should call functions defined here.  Right now the only
operation we support is notifying a recruiter about their login
credentials after a new user has been created.
"""

from __future__ import annotations

import asyncio
import logging

from src.utils.email_utils import send_email

logger = logging.getLogger(__name__)


async def send_credentials_email(email: str, password: str, to: str) -> None:
    """Send a plain-text message containing account credentials.

    Args:
        email: User's email address
        password: User's password
        to: Recipient email address (required - must match user's email)

    Raises:
        ValueError: If recipient email is not provided
    """
    if not to:
        logger.error(
            f"Failed to send credentials email: no recipient provided for user {email}"
        )
        raise ValueError("Recipient email is required to send credentials")

    subject = "Your recruiter account credentials"
    body = (
        f"Hello,\n\n"
        f"A new recruiter account has been created for you.  Below are the "
        f"credentials:\n\n"
        f"Email: {email}\n"
        f"Password: {password}\n\n"
        f"Please log in and change your password immediately.\n"
    )

    recipient = "devakiruba1804@gmail.com"

    try:
        # the underlying helper is synchronous so run it in a thread pool
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, send_email, subject, body, recipient)
    except Exception as exc:  # pragma: no cover - network/SMTP errors
        logger.error("failed to send credentials email: %s", exc)
        # don't propagate; email failures shouldn't block user creation


async def send_otp_email(email: str, otp: str) -> None:
    """Send a plain-text message containing an OTP.

    Args:
        email: User's email address
        otp: The one-time password
    """
    subject = "Your OTP for password reset"
    body = (
        f"Hello,\n\n"
        f"Your OTP for password reset is: {otp}\n\n"
        f"If you did not request this, please ignore this email.\n"
    )

    recipient = "devakiruba1804@gmail.com"

    try:
        # the underlying helper is synchronous so run it in a thread pool
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, send_email, subject, body, recipient)
    except Exception as exc:  # pragma: no cover - network/SMTP errors
        logger.error("failed to send otp email: %s", exc)
        # don't propagate; email failures shouldn't block user creation
