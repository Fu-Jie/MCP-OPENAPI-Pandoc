"""MCP Tools for Pandoc Bridge."""

from typing import Any

from src.config import get_settings
from src.core.converter import ConversionService


async def convert_text_tool(
    content: str,
    from_format: str,
    to_format: str,
    standalone: bool = True,
) -> dict[str, Any]:
    """Convert text from one format to another.

    Args:
        content: The text content to convert
        from_format: Source format (e.g., 'markdown', 'html', 'latex')
        to_format: Target format (e.g., 'html', 'pdf', 'docx')
        standalone: Generate standalone document (default: True)

    Returns:
        Dictionary with success status, converted content, and content type
    """
    from src.core.converter import ConversionOptions

    service = ConversionService()
    options = ConversionOptions(standalone=standalone)

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
        return {
            "success": False,
            "error": str(e),
        }


async def convert_file_base64_tool(
    file_base64: str,
    filename: str,
    to_format: str,
) -> dict[str, Any]:
    """Convert a base64-encoded file to another format.

    Args:
        file_base64: Base64-encoded file content
        filename: Original filename (used to detect source format)
        to_format: Target format (e.g., 'html', 'pdf', 'markdown')

    Returns:
        Dictionary with success status, converted content (base64), and content type
    """
    service = ConversionService()

    try:
        result = await service.convert_file_base64(
            file_base64=file_base64,
            filename=filename,
            to_format=to_format,
        )
        result_dict = result.to_dict()
        return {
            "success": True,
            "content_base64": result_dict["content"],
            "content_type": result.content_type,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def list_formats_tool() -> dict[str, list[str]]:
    """Get list of supported input and output formats.

    Returns:
        Dictionary with input and output format lists
    """
    service = ConversionService()
    formats = await service.get_formats()
    return formats.to_dict()


async def get_service_info_tool() -> dict[str, str]:
    """Get service and Pandoc version information.

    Returns:
        Dictionary with service version and Pandoc version
    """
    settings = get_settings()
    service = ConversionService()
    pandoc_version = await service.get_pandoc_version()

    return {
        "service_version": settings.service_version,
        "pandoc_version": pandoc_version,
    }
