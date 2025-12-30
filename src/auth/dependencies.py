"""Shared authentication dependencies for REST and MCP."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.bearer import TokenPayload, extract_bearer_token, verify_token
from src.core.exceptions import AuthenticationError

# HTTP Bearer security scheme for OpenAPI docs
http_bearer = HTTPBearer(auto_error=False)


async def require_auth_http(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)] = None,
) -> TokenPayload:
    """Dependency to require authentication for HTTP requests.

    This is used as a FastAPI dependency for protected endpoints.

    Args:
        request: The FastAPI request object
        credentials: HTTP Bearer credentials from header

    Returns:
        TokenPayload with decoded token claims

    Raises:
        AuthenticationError: If authentication fails
    """
    if credentials is None:
        # Try to get from header directly
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise AuthenticationError()
        token = extract_bearer_token(auth_header)
    else:
        token = credentials.credentials

    return verify_token(token)


async def get_optional_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)] = None,
) -> TokenPayload | None:
    """Dependency for optional authentication.

    Returns TokenPayload if valid token provided, None otherwise.
    Does not raise errors for missing tokens.

    Args:
        request: The FastAPI request object
        credentials: Optional HTTP Bearer credentials

    Returns:
        TokenPayload if authenticated, None otherwise
    """
    if credentials is None:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        try:
            token = extract_bearer_token(auth_header)
        except AuthenticationError:
            return None
    else:
        token = credentials.credentials

    try:
        return verify_token(token)
    except AuthenticationError:
        return None


async def require_auth_mcp(request: Request) -> TokenPayload:
    """Dependency to require authentication for MCP requests.

    This extracts the token from the request headers and validates it.
    Used within MCP tool handlers.

    Args:
        request: The Starlette/FastAPI request object

    Returns:
        TokenPayload with decoded token claims

    Raises:
        AuthenticationError: If authentication fails
    """
    auth_header = request.headers.get("Authorization")
    token = extract_bearer_token(auth_header)
    return verify_token(token)


# Type aliases for dependency injection
RequireAuth = Annotated[TokenPayload, Depends(require_auth_http)]
OptionalAuth = Annotated[TokenPayload | None, Depends(get_optional_auth)]
