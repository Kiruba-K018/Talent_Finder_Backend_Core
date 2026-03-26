"""Helper methods for sending email messages.

The project uses a simple SMTP-based sender that reads settings from
:class:`src.config.settings.Settings`. All emails must have an explicit
recipient address specified to prevent accidental delivery to default recipients.
"""

from __future__ import annotations

import contextlib
import logging
import smtplib
from email.message import EmailMessage

from src.config.settings import setting

logger = logging.getLogger(__name__)


def send_email(subject: str, body: str, to_email: str) -> None:
    """Send a plain-text email using SMTP.

    Args:
        subject: Email subject line
        body: Email body content
        to_email: Recipient email address (required - no default fallback)

    Raises:
        ValueError: If to_email is not provided
    """
    if not to_email:
        logger.warning("Attempted to send email without recipient - message not sent")
        raise ValueError("Email recipient (to_email) is required and cannot be None")

    sender = setting.email_from or setting.email_user or ""
    recipient = to_email

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)

    host = setting.email_host
    port = setting.email_port
    user = setting.email_user
    password = setting.email_password

    with smtplib.SMTP(host, port) as server:
        # TLS is common; if the server doesn't support it this will be a no-op
        with contextlib.suppress(Exception):
            server.starttls()

        if user and password:
            server.login(user, password)

        server.send_message(msg)
