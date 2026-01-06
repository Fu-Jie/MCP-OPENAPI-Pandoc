"""MCP Tools for Pandoc Bridge."""

import logging
from typing import Any

from src.auth.bearer import TokenPayload, extract_bearer_token, verify_token
from src.config import get_settings
from src.core.converter import ConversionService
from src.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


def verify_mcp_auth(auth_header: str | None) -> TokenPayload | None:
    """Verify MCP request authentication."""
    if not auth_header:
        return None
    try:
        token = extract_bearer_token(auth_header)
        return verify_token(token)
    except AuthenticationError:
        raise


async def convert_text_tool(
    content: str,
    from_format: str,
    to_format: str,
    standalone: bool = True,
    pdf_engine: str | None = None,
    auth_header: str | None = None,
) -> dict[str, Any]:
    """Convert text from one format to another.

    Args:
        content: The text content to convert
        from_format: Source format (e.g., 'markdown', 'html', 'latex')
        to_format: Target format (e.g., 'html', 'pdf', 'docx')
        standalone: Generate standalone document (default: True)
        pdf_engine: PDF engine: pdflatex, xelatex, lualatex (xelatex for CJK)
        auth_header: Optional authorization header

    Returns:
        Dictionary with success status, converted content, and content type
    """
    from src.core.converter import ConversionOptions

    logger.info("MCP convert_text: %s -> %s", from_format, to_format)

    service = ConversionService()
    options = ConversionOptions(standalone=standalone, pdf_engine=pdf_engine)

    try:
        result = await service.convert_text(
            content=content,
            from_format=from_format,
            to_format=to_format,
            options=options,
        )
        result_dict = result.to_dict()
        return {
            "success": True,
            "content": result_dict["content"],
            "content_type": result.content_type,
            "is_binary": result.is_binary,
        }
    except Exception as e:
        logger.error("MCP convert_text error: %s", str(e))
        return {
            "success": False,
            "error": str(e),
        }


async def convert_file_base64_tool(
    file_base64: str,
    filename: str,
    to_format: str,
    pdf_engine: str | None = None,
    auth_header: str | None = None,
) -> dict[str, Any]:
    """Convert a base64-encoded file to another format.

    Args:
        file_base64: Base64-encoded file content
        filename: Original filename (used to detect source format)
        to_format: Target format (e.g., 'html', 'pdf', 'markdown')
        pdf_engine: PDF engine for PDF output (xelatex for CJK)
        auth_header: Optional authorization header

    Returns:
        Dictionary with success status, converted content (base64), and content type
    """
    from src.core.converter import ConversionOptions

    logger.info("MCP convert_file_base64: %s -> %s", filename, to_format)

    service = ConversionService()
    options = ConversionOptions(pdf_engine=pdf_engine) if pdf_engine else None

    try:
        result = await service.convert_file_base64(
            file_base64=file_base64,
            filename=filename,
            to_format=to_format,
            options=options,
        )
        result_dict = result.to_dict()
        return {
            "success": True,
            "content_base64": result_dict["content"],
            "content_type": result.content_type,
        }
    except Exception as e:
        logger.error("MCP convert_file_base64 error: %s", str(e))
        return {
            "success": False,
            "error": str(e),
        }


async def list_formats_tool() -> dict[str, list[str]]:
    """Get list of supported input and output formats.

    Returns:
        Dictionary with input and output format lists
    """
    logger.debug("MCP list_formats called")
    service = ConversionService()
    formats = await service.get_formats()
    return formats.to_dict()


async def get_service_info_tool() -> dict[str, str]:
    """Get service and Pandoc version information.

    Returns:
        Dictionary with service version and Pandoc version
    """
    logger.debug("MCP get_service_info called")
    settings = get_settings()
    service = ConversionService()
    pandoc_version = await service.get_pandoc_version()

    return {
        "service_version": settings.service_version,
        "pandoc_version": pandoc_version,
    }
