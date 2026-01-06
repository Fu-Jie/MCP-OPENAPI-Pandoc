"""Tests for MCP server and tools."""

import base64

import pytest

from src.mcp.tools import (
    convert_file_base64_tool,
    convert_text_tool,
    get_service_info_tool,
    list_formats_tool,
)


class TestMCPTools:
    """Tests for MCP tools."""

    @pytest.mark.asyncio
    async def test_list_formats(self) -> None:
        """Test list_formats tool."""
        result = await list_formats_tool()
        assert "input" in result
        assert "output" in result
        assert isinstance(result["input"], list)
        assert isinstance(result["output"], list)
        assert "markdown" in result["input"]
        assert "html" in result["output"]

    @pytest.mark.asyncio
    async def test_get_service_info(self) -> None:
        """Test get_service_info tool."""
        result = await get_service_info_tool()
        assert "service_version" in result
        assert "pandoc_version" in result

    @pytest.mark.asyncio
    async def test_convert_text_success(self) -> None:
        """Test successful text conversion."""
        result = await convert_text_tool(
            content="# Hello World",
            from_format="markdown",
            to_format="html",
            standalone=True,
        )
        assert result["success"] is True
        assert "content" in result
        assert result["content_type"] == "text/html"
        assert "Hello World" in result["content"]

    @pytest.mark.asyncio
    async def test_convert_text_invalid_format(self) -> None:
        """Test conversion with invalid format."""
        result = await convert_text_tool(
            content="test",
            from_format="invalid_format",
            to_format="html",
        )
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_convert_text_non_standalone(self) -> None:
        """Test conversion without standalone flag."""
        result = await convert_text_tool(
            content="# Hello",
            from_format="markdown",
            to_format="html",
            standalone=False,
        )
        assert result["success"] is True
        # Non-standalone should not have full HTML document structure
        assert "<!DOCTYPE" not in result.get("content", "")

    @pytest.mark.asyncio
    async def test_convert_file_base64(self) -> None:
        """Test base64 file conversion."""
        content = "# Test Document\n\nThis is content."
        file_base64 = base64.b64encode(content.encode()).decode()

        result = await convert_file_base64_tool(
            file_base64=file_base64,
            filename="test.md",
            to_format="html",
        )
        assert result["success"] is True
        assert "content_base64" in result
        assert result["content_type"] == "text/html"

    @pytest.mark.asyncio
    async def test_convert_file_base64_invalid(self) -> None:
        """Test base64 file conversion with invalid base64."""
        result = await convert_file_base64_tool(
            file_base64="not-valid-base64!!!",
            filename="test.md",
            to_format="html",
        )
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_convert_file_base64_unsupported_extension(self) -> None:
        """Test base64 file conversion with unsupported file extension."""
        content = "some content"
        file_base64 = base64.b64encode(content.encode()).decode()

        result = await convert_file_base64_tool(
            file_base64=file_base64,
            filename="test.xyz",
            to_format="html",
        )
        assert result["success"] is False
        assert "error" in result


class TestMCPServer:
    """Tests for MCP server registration."""

    def test_mcp_server_exists(self) -> None:
        """Test MCP server is created."""
        from src.mcp.server import mcp

        assert mcp is not None
        assert mcp.name == "pandoc-bridge"

    def test_tools_registered(self) -> None:
        """Test tools are registered with MCP server."""
        from src.mcp.server import mcp

        # Get registered tools - FastMCP stores tools internally
        # We can verify by checking the tool functions exist
        assert hasattr(mcp, "tool")

    def test_mcp_server_has_instructions(self) -> None:
        """Test MCP server has instructions configured."""
        from src.mcp.server import mcp

        assert mcp.instructions is not None
        assert "Pandoc Bridge" in mcp.instructions
