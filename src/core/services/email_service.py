"""Service layer for application-specific email operations.

Rather than dealing with low-level SMTP details, other parts of the
codebase should call functions defined here.  Right now the only
operation we support is notifying a recruiter about their login
credentials after a new user has been created.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from src.config.settings import setting
from src.utils.email_utils import send_email

logger = logging.getLogger(__name__)


async def send_credentials_email(
    email: str, password: str, to: Optional[str] = None
) -> None:
    """Send a plain-text message containing account credentials.

    The ``to`` argument is ignored by default; all messages are routed to
    ``setting.email_default_recipient`` so that development activity does
    not accidentally hit real inboxes.  A real deployment would either pass
    ``email`` here or make the recipient configurable per-user.
    """
    subject = "Your recruiter account credentials"
    body = (
        f"Hello,\n\n"
        f"A new recruiter account has been created for you.  Below are the "
        f"credentials:\n\n"
        f"Email: {email}\n"
        f"Password: {password}\n\n"
        f"Please log in and change your password immediately.\n"
    )

    # always send to configured default recipient in current settings
    recipient = to or setting.email_default_recipient

    try:
        # the underlying helper is synchronous so run it in a thread pool
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, send_email, subject, body, recipient)
    except Exception as exc:  # pragma: no cover - network/SMTP errors
        logger.error("failed to send credentials email: %s", exc)
        # don't propagate; email failures shouldn't block user creation
