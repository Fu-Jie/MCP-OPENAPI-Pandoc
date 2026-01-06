"""Shared authentication dependencies for REST and MCP."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.bearer import TokenPayload, extract_bearer_token, verify_api_key
from src.core.exceptions import AuthenticationError

# HTTP Bearer security scheme for OpenAPI docs
http_bearer = HTTPBearer(auto_error=False)


async def require_auth_http(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(http_bearer)
    ] = None,
) -> TokenPayload:
    """Dependency to require API key authentication for HTTP requests."""
    if credentials is None:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise AuthenticationError()
        token = extract_bearer_token(auth_header)
    else:
        token = credentials.credentials

    return verify_api_key(token)


async def get_optional_auth(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(http_bearer)
    ] = None,
) -> TokenPayload | None:
    """Dependency for optional authentication.

    Returns TokenPayload if valid API key provided, None otherwise.
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
        return verify_api_key(token)
    except AuthenticationError:
        return None


async def require_auth_mcp(request: Request) -> TokenPayload:
    """Dependency to require API key authentication for MCP requests."""
    auth_header = request.headers.get("Authorization")
    token = extract_bearer_token(auth_header)
    return verify_api_key(token)


# Type aliases for dependency injection
RequireAuth = Annotated[TokenPayload, Depends(require_auth_http)]
OptionalAuth = Annotated[TokenPayload | None, Depends(get_optional_auth)]
