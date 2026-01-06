"""FastMCP Server for Pandoc Bridge."""

import json
from typing import Any

from fastmcp import FastMCP

from src.config import get_settings
from src.mcp.tools import (
    convert_file_base64_tool,
    convert_text_tool,
    get_service_info_tool,
    list_formats_tool,
)

settings = get_settings()

# Create FastMCP server
mcp = FastMCP(
    name="pandoc-bridge",
    instructions="""
    Pandoc Bridge MCP Server - Document format conversion service.
    
    This server provides tools for converting documents between various formats
    using Pandoc as the conversion engine.
    
    Available tools:
    - convert_text: Convert text content between formats
    - convert_file_base64: Convert base64-encoded files
    - list_formats: Get supported input/output formats
    - get_service_info: Get version information
    
    Available resources:
    - formats://list: JSON list of supported formats
    - formats://matrix: Format conversion compatibility matrix
    """,
)


# Register tools
@mcp.tool()
async def convert_text(
    content: str,
    from_format: str,
    to_format: str,
    standalone: bool = True,
    pdf_engine: str | None = None,
) -> dict[str, Any]:
    """Convert text from one format to another.

    Args:
        content: The text content to convert
        from_format: Source format (e.g., 'markdown', 'html', 'latex')
        to_format: Target format (e.g., 'html', 'pdf', 'docx')
        standalone: Generate standalone document (default: True)
        pdf_engine: PDF engine: pdflatex, xelatex (for CJK), lualatex

    Returns:
        Dictionary with success status, converted content, and content type
    """
    return await convert_text_tool(content, from_format, to_format, standalone, pdf_engine)


@mcp.tool()
async def convert_file_base64(
    file_base64: str,
    filename: str,
    to_format: str,
    pdf_engine: str | None = None,
) -> dict[str, Any]:
    """Convert a base64-encoded file to another format.

    Args:
        file_base64: Base64-encoded file content
        filename: Original filename (used to detect source format)
        to_format: Target format (e.g., 'html', 'pdf', 'markdown')
        pdf_engine: PDF engine for PDF output (xelatex for CJK support)

    Returns:
        Dictionary with success status, converted content (base64), and content type
    """
    return await convert_file_base64_tool(file_base64, filename, to_format, pdf_engine)


@mcp.tool()
async def list_formats() -> dict[str, list[str]]:
    """Get list of supported input and output formats.

    Returns:
        Dictionary with input and output format lists
    """
    return await list_formats_tool()


@mcp.tool()
async def get_service_info() -> dict[str, str]:
    """Get service and Pandoc version information.

    Returns:
        Dictionary with service version and Pandoc version
    """
    return await get_service_info_tool()


# Register resources
@mcp.resource("formats://list")
async def formats_list_resource() -> str:
    """Get format list as JSON resource."""
    formats = await list_formats_tool()
    return json.dumps(formats, indent=2)


@mcp.resource("formats://matrix")
async def formats_matrix_resource() -> str:
    """Get format conversion compatibility matrix."""
    from src.core.formats import get_format_manager

    manager = get_format_manager()
    await manager.get_formats()  # Ensure formats are loaded
    matrix = manager.get_format_matrix()
    return json.dumps(matrix, indent=2)
