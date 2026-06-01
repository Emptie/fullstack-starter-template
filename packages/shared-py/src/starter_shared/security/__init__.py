"""JWT security utilities.

Provides token creation and verification for JWT + Refresh Token auth.
Phase 1 skeleton — full implementation in Phase 2 (auth feature).
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from starter_shared.config import settings


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived JWT access token.

    Args:
        data: Payload to encode (typically {"sub": user_id}).
        expires_delta: Custom expiration time. Defaults to settings.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.security.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.security.secret_key, algorithm=settings.security.algorithm)


def create_refresh_token(data: dict) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        data: Payload to encode (typically {"sub": user_id}).

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.security.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.security.secret_key, algorithm=settings.security.algorithm)


def verify_token(token: str, token_type: str = "access") -> dict | None:
    """Verify a JWT token and return its payload.

    Args:
        token: JWT string to verify.
        token_type: Expected token type ("access" or "refresh").

    Returns:
        Decoded payload dict, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.security.secret_key, algorithms=[settings.security.algorithm])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None
