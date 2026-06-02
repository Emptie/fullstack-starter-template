"""Email sending service with SMTP / console fallback.

If SMTP is configured (smtp_host, smtp_user, smtp_password), sends real email.
Otherwise, prints the message to stdout for development convenience.
"""

import logging
import smtplib
from email.mime.text import MIMEText

from starter_shared.config import settings

logger = logging.getLogger(__name__)


async def send_password_reset_email(to_email: str, token: str) -> None:
    """Send a password reset email or print the reset link to console.

    Args:
        to_email: Recipient email address.
        token: Raw password reset token (not the hash).
    """
    reset_url = f"{settings.frontend_base_url}/reset-password?token={token}"
    subject = "Password Reset Request"
    body = (
        f"You requested a password reset.\n\n"
        f"Click the link below to set a new password:\n"
        f"{reset_url}\n\n"
        f"This link expires in {settings.security.password_reset_expire_hours} hour(s).\n"
        f"If you did not request this, ignore this email.\n"
    )

    if settings.smtp.is_configured:
        await _send_smtp(to_email, subject, body)
    else:
        _send_console(to_email, subject, body, reset_url, token)


async def _send_smtp(to_email: str, subject: str, body: str) -> None:
    """Send email via SMTP."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.smtp.smtp_from
    msg["To"] = to_email

    try:
        if settings.smtp.smtp_use_tls:
            server = smtplib.SMTP(settings.smtp.smtp_host, settings.smtp.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.smtp.smtp_host, settings.smtp.smtp_port)

        server.login(settings.smtp.smtp_user, settings.smtp.smtp_password)
        server.sendmail(settings.smtp.smtp_from, [to_email], msg.as_string())
        server.quit()
        logger.info("Password reset email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
        raise


def _send_console(
    to_email: str, subject: str, body: str, reset_url: str, token: str
) -> None:
    """Print the reset link to console (development fallback)."""
    separator = "=" * 60
    logger.info(
        "\n%s\n[DEV EMAIL] To: %s | Subject: %s\nReset URL: %s\nToken: %s\n%s",
        separator, to_email, subject, reset_url, token, separator,
    )
    # Also print to stdout so it's visible even without logging config
    print(f"\n{separator}")
    print(f"[DEV EMAIL] To: {to_email} | Subject: {subject}")
    print(f"Reset URL: {reset_url}")
    print(f"Token: {token}")
    print(f"{separator}\n")
