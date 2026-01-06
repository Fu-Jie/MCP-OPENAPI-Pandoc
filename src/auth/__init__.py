"""Authentication module."""

# Lazy imports to avoid circular dependencies
__all__ = [
    "verify_token",
    "create_token",
    "TokenPayload",
    "require_auth_http",
    "require_auth_mcp",
    "get_optional_auth",
]


def __getattr__(name: str):
    if name in ("TokenPayload", "create_token", "verify_token"):
        from src.auth.bearer import TokenPayload, create_token, verify_token
        return {"TokenPayload": TokenPayload, "create_token": create_token, "verify_token": verify_token}[name]
    if name in ("get_optional_auth", "require_auth_http", "require_auth_mcp"):
        from src.auth.dependencies import get_optional_auth, require_auth_http, require_auth_mcp
        return {"get_optional_auth": get_optional_auth, "require_auth_http": require_auth_http, "require_auth_mcp": require_auth_mcp}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
