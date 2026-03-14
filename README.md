# Talent_Finder_Backend_Core
The core backend services of the talentfinder - resume sourcing and shortlisting platform

## Configuration

This project uses a `.env` file to configure database connections, API keys,
and other runtime settings via :class:`pydantic_settings.BaseSettings`.

### Email / SMTP settings

Several new environment variables control outbound email behaviour.  In
development all messages are routed to a single address defined by
`EMAIL_DEFAULT_RECIPIENT` to avoid accidentally spamming real users.

```env
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=sender@example.com
EMAIL_PASSWORD=...
EMAIL_FROM=no-reply@example.com
EMAIL_DEFAULT_RECIPIENT=recruiters@example.com
```

The application currently sends recruiter credentials after a new user
is created; when the service matures the recipient logic can be made
per-user.
