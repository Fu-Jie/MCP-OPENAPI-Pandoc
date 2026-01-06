"""Pytest configuration and fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

# Set test API key before importing app
os.environ["API_KEYS"] = "sk-test-key:2099-12-31"

from src.main import app
from src.middleware.rate_limit import RateLimitMiddleware

# Disable rate limiting for tests
for middleware in app.user_middleware:
    if middleware.cls == RateLimitMiddleware:
        app.user_middleware.remove(middleware)
        break


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_token() -> str:
    """Create a valid API key."""
    return "sk-test-key"


@pytest.fixture
def admin_token() -> str:
    """Create an admin API key (same as auth_token, all keys are admin)."""
    return "sk-test-key"


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    """Create admin authorization headers."""
    return {"Authorization": f"Bearer {admin_token}"}
