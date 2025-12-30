"""Tests for REST API endpoints."""

from fastapi.testclient import TestClient


class TestPublicEndpoints:
    """Tests for public endpoints."""

    def test_get_service_info(self, client: TestClient) -> None:
        """Test service info endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "pandoc_version" in data
        assert "timestamp" in data

    def test_list_formats(self, client: TestClient) -> None:
        """Test format listing endpoint."""
        response = client.get("/api/v1/formats")
        assert response.status_code == 200
        data = response.json()
        assert "input" in data
        assert "output" in data
        assert isinstance(data["input"], list)
        assert isinstance(data["output"], list)
        assert "markdown" in data["input"]
        assert "html" in data["output"]


class TestConvertText:
    """Tests for text conversion endpoint."""

    def test_convert_text_unauthorized(self, client: TestClient) -> None:
        """Test that conversion requires authentication."""
        response = client.post(
            "/api/v1/convert/text",
            json={
                "content": "# Hello",
                "from_format": "markdown",
                "to_format": "html",
            },
        )
        assert response.status_code == 401

    def test_convert_markdown_to_html(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test converting markdown to HTML."""
        response = client.post(
            "/api/v1/convert/text",
            headers=auth_headers,
            json={
                "content": "# Hello World\n\nThis is a test.",
                "from_format": "markdown",
                "to_format": "html",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "content_type" in data
        assert data["content_type"] == "text/html"
        assert data["is_binary"] is False
        assert "<h1" in data["content"]
        assert "Hello World" in data["content"]

    def test_convert_html_to_markdown(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test converting HTML to markdown."""
        response = client.post(
            "/api/v1/convert/text",
            headers=auth_headers,
            json={
                "content": "<h1>Title</h1><p>Paragraph</p>",
                "from_format": "html",
                "to_format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "Title" in data["content"]

    def test_convert_invalid_format(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test error on invalid format."""
        response = client.post(
            "/api/v1/convert/text",
            headers=auth_headers,
            json={
                "content": "test",
                "from_format": "invalid_format",
                "to_format": "html",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "FORMAT_NOT_SUPPORTED"


class TestConvertFile:
    """Tests for file conversion endpoint."""

    def test_convert_file_unauthorized(self, client: TestClient) -> None:
        """Test that file conversion requires authentication."""
        response = client.post(
            "/api/v1/convert/file",
            data={"to_format": "html"},
            files={"file": ("test.md", b"# Hello", "text/markdown")},
        )
        assert response.status_code == 401

    def test_convert_markdown_file(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test converting a markdown file to HTML."""
        response = client.post(
            "/api/v1/convert/file",
            headers=auth_headers,
            data={"to_format": "html"},
            files={
                "file": (
                    "test.md",
                    b"# Test Document\n\nContent here.",
                    "text/markdown",
                )
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        content = response.content.decode()
        assert "Test Document" in content


class TestAuthentication:
    """Tests for authentication."""

    def test_invalid_token(self, client: TestClient) -> None:
        """Test rejection of invalid token."""
        response = client.post(
            "/api/v1/convert/text",
            headers={"Authorization": "Bearer invalid-token"},
            json={
                "content": "test",
                "from_format": "markdown",
                "to_format": "html",
            },
        )
        assert response.status_code == 401

    def test_admin_scope(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        """Test that admin scope grants access."""
        response = client.post(
            "/api/v1/convert/text",
            headers=admin_headers,
            json={
                "content": "# Admin Test",
                "from_format": "markdown",
                "to_format": "html",
            },
        )
        assert response.status_code == 200


class TestOpenAPI:
    """Tests for OpenAPI documentation."""

    def test_openapi_json(self, client: TestClient) -> None:
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_docs_available(self, client: TestClient) -> None:
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200
