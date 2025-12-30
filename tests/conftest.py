"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.auth.bearer import create_token
from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_token() -> str:
    """Create a valid authentication token."""
    return create_token(
        subject="test-client",
        scopes=["formats:read", "convert:text", "convert:file"],
    )


@pytest.fixture
def admin_token() -> str:
    """Create an admin authentication token."""
    return create_token(
        subject="admin-client",
        scopes=["admin"],
    )


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    """Create admin authorization headers."""
    return {"Authorization": f"Bearer {admin_token}"}
