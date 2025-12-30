"""JWT Bearer token handling."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel

from src.config import get_settings
from src.core.exceptions import AuthenticationError, AuthorizationError


class TokenPayload(BaseModel):
    """JWT token payload model."""

    sub: str  # client-id
    scopes: list[str] = []
    exp: datetime | None = None
    iat: datetime | None = None

    def has_scope(self, scope: str) -> bool:
        """Check if token has a specific scope."""
        if "admin" in self.scopes:
            return True
        return scope in self.scopes

    def require_scope(self, scope: str) -> None:
        """Require a specific scope, raise AuthorizationError if missing."""
        if not self.has_scope(scope):
            raise AuthorizationError(
                f"Missing required scope: {scope}",
                required_scopes=[scope],
            )


def verify_token(token: str) -> TokenPayload:
    """Verify and decode a JWT token.

    Args:
        token: The JWT token string

    Returns:
        TokenPayload with decoded claims

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except ExpiredSignatureError as e:
        raise AuthenticationError("Token has expired") from e
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {e}") from e


def create_token(
    subject: str,
    scopes: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a new JWT token.

    Args:
        subject: The subject (client-id) for the token
        scopes: List of permission scopes
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    settings = get_settings()
    scopes = scopes or []

    now = datetime.now(UTC)
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_expire_hours)

    expire = now + expires_delta

    payload: dict[str, Any] = {
        "sub": subject,
        "scopes": scopes,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def extract_bearer_token(authorization: str | None) -> str:
    """Extract token from Authorization header.

    Args:
        authorization: The Authorization header value

    Returns:
        The token string

    Raises:
        AuthenticationError: If header is missing or malformed
    """
    if not authorization:
        raise AuthenticationError("Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2:
        raise AuthenticationError("Invalid Authorization header format")

    scheme, token = parts
    if scheme.lower() != "bearer":
        raise AuthenticationError("Invalid authentication scheme, expected 'Bearer'")

    return token
