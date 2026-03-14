"""Top-level services package.

Individual service modules are exposed here to make imports slightly
shorter.  New services should be added as they are created.
"""

from .email_service import send_credentials_email
# other services are imported in subpackages where appropriate

__all__ = ["send_credentials_email"]
