"""Authentication module."""

__all__ = [
    "TokenPayload",
    "verify_api_key",
    "verify_token",
    "extract_bearer_token",
    "require_auth_http",
    "require_auth_mcp",
    "get_optional_auth",
]


def __getattr__(name: str):
    if name in ("TokenPayload", "verify_api_key", "verify_token", "extract_bearer_token"):
        from src.auth.bearer import (
            TokenPayload,
            extract_bearer_token,
            verify_api_key,
            verify_token,
        )

        return {
            "TokenPayload": TokenPayload,
            "verify_api_key": verify_api_key,
            "verify_token": verify_token,
            "extract_bearer_token": extract_bearer_token,
        }[name]
    if name in ("get_optional_auth", "require_auth_http", "require_auth_mcp"):
        from src.auth.dependencies import (
            get_optional_auth,
            require_auth_http,
            require_auth_mcp,
        )

        return {
            "get_optional_auth": get_optional_auth,
            "require_auth_http": require_auth_http,
            "require_auth_mcp": require_auth_mcp,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
