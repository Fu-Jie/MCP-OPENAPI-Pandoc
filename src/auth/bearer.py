"""API Key authentication handling."""

from datetime import date

from pydantic import BaseModel

from src.config import get_settings
from src.core.exceptions import AuthenticationError


class TokenPayload(BaseModel):
    """Token payload model for authenticated requests."""

    sub: str  # API key identifier
    scopes: list[str] = ["admin"]  # API keys have full access

    def has_scope(self, scope: str) -> bool:
        """Check if token has a specific scope."""
        if "admin" in self.scopes:
            return True
        return scope in self.scopes

    def require_scope(self, scope: str) -> None:
        """Require a specific scope, raise error if missing."""
        from src.core.exceptions import AuthorizationError

        if not self.has_scope(scope):
            raise AuthorizationError(
                f"Missing required scope: {scope}",
                required_scopes=[scope],
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


def verify_api_key(api_key: str) -> TokenPayload:
    """Verify API key and check expiration.

    Args:
        api_key: The API key string (e.g., sk-xxx)

    Returns:
        TokenPayload if valid

    Raises:
        AuthenticationError: If API key is invalid or expired
    """
    settings = get_settings()
    api_keys = settings.get_api_keys()

    if not api_keys:
        raise AuthenticationError("No API keys configured")

    if api_key not in api_keys:
        raise AuthenticationError("Invalid API key")

    # Check expiration
    expiry = api_keys[api_key]
    if expiry:
        try:
            expiry_date = date.fromisoformat(expiry)
            if date.today() > expiry_date:
                raise AuthenticationError(f"API key expired on {expiry}")
        except ValueError:
            # Invalid date format, treat as no expiry
            pass

    return TokenPayload(sub=api_key)


# Alias for backward compatibility
def verify_token(token: str) -> TokenPayload:
    """Verify token (API key)."""
    return verify_api_key(token)
