"""Helper methods for sending email messages.

The project currently uses a simple SMTP-based sender that reads
settings from :class:`src.config.settings.Settings`.  All messages
are routed to a fixed recipient (``email_default_recipient``); this
keeps testing safe while the infrastructure is immature.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from src.config.settings import setting


def send_email(subject: str, body: str, to_email: str | None = None) -> None:
    """Send a plain-text email using SMTP.

    ``to_email`` is ignored by default; the settings object defines a
    single address where all messages are delivered.  This is intentional
    while the codebase is in development.  The caller may pass a value to
    override for a future when multiple recipients are supported.
    """
    sender = setting.email_from or setting.email_user or ""
    recipient = to_email or setting.email_default_recipient

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
        try:
            server.starttls()
        except Exception:  # pragma: no cover - network dependent
            pass

        if user and password:
            server.login(user, password)

        server.send_message(msg)
