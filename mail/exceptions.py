class MailClientError(Exception):
    """Base exception for mail client errors."""


class MessageNotFoundError(MailClientError):
    """Raised when a matching message is not found."""


class VerificationLinkNotFoundError(MailClientError):
    """Raised when a verification link cannot be extracted from a message."""
