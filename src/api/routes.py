"""REST API routes."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse

from src.api.schemas import (
    ConvertStreamRequest,
    ConvertTextRequest,
    ConvertTextResponse,
    FormatListResponse,
    HealthCheck,
    ServiceInfo,
)
from src.auth.dependencies import OptionalAuth, RequireAuth
from src.config import get_settings
from src.core.converter import ConversionOptions as CoreConversionOptions
from src.core.converter import ConversionService
from src.core.exceptions import FileSizeError

router = APIRouter()


def get_conversion_service() -> ConversionService:
    """Dependency to get conversion service."""
    return ConversionService()


@router.get("/", response_model=ServiceInfo, tags=["Info"])
async def get_service_info() -> ServiceInfo:
    """Get service information."""
    settings = get_settings()
    return ServiceInfo(
        name=settings.service_name,
        version=settings.service_version,
        endpoints={
            "health": "/health",
            "formats": "/api/v1/formats",
            "convert_text": "/api/v1/convert/text",
            "convert_file": "/api/v1/convert/file",
            "convert_stream": "/api/v1/convert/stream",
            "mcp": "/mcp",
            "docs": "/docs",
        },
    )


@router.get("/health", response_model=HealthCheck, tags=["Info"])
async def health_check(
    service: Annotated[ConversionService, Depends(get_conversion_service)],
) -> HealthCheck:
    """Health check endpoint."""
    pandoc_version = await service.get_pandoc_version()
    return HealthCheck(
        status="healthy",
        pandoc_version=pandoc_version,
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get("/api/v1/formats", response_model=FormatListResponse, tags=["Formats"])
async def list_formats(
    service: Annotated[ConversionService, Depends(get_conversion_service)],
    auth: OptionalAuth = None,
) -> FormatListResponse:
    """Get list of supported input and output formats.

    This endpoint is public but can optionally include authentication.
    """
    formats = await service.get_formats()
    return FormatListResponse(
        input=formats.input,
        output=formats.output,
    )


@router.post(
    "/api/v1/convert/text", response_model=ConvertTextResponse, tags=["Convert"]
)
async def convert_text(
    request: ConvertTextRequest,
    auth: RequireAuth,
    service: Annotated[ConversionService, Depends(get_conversion_service)],
) -> ConvertTextResponse:
    """Convert text content from one format to another.

    Requires authentication with 'convert:text' or 'admin' scope.
    """
    auth.require_scope("convert:text")

    options = None
    if request.options:
        options = CoreConversionOptions(
            standalone=request.options.standalone,
            table_of_contents=request.options.table_of_contents,
            number_sections=request.options.number_sections,
            wrap=request.options.wrap,
            columns=request.options.columns,
        )

    result = await service.convert_text(
        content=request.content,
        from_format=request.from_format,
        to_format=request.to_format,
        options=options,
    )

    # Return text content directly or base64 for binary
    result_dict = result.to_dict()
    return ConvertTextResponse(
        content=result_dict["content"],
        content_type=result.content_type,
        is_binary=result.is_binary,
    )


@router.post("/api/v1/convert/file", tags=["Convert"])
async def convert_file(
    file: Annotated[UploadFile, File(description="File to convert")],
    to_format: Annotated[str, Form(description="Target format")],
    auth: RequireAuth,
    service: Annotated[ConversionService, Depends(get_conversion_service)],
    from_format: Annotated[
        str | None, Form(description="Source format (optional)")
    ] = None,
) -> Response:
    """Convert an uploaded file to another format.

    Requires authentication with 'convert:file' or 'admin' scope.
    Returns the converted file as a download.
    """
    auth.require_scope("convert:file")

    settings = get_settings()

    # Read file content
    file_content = await file.read()

    # Check file size
    if len(file_content) > settings.max_file_size_bytes:
        raise FileSizeError(len(file_content), settings.max_file_size_bytes)

    filename = file.filename or "document"

    result = await service.convert_file(
        file_bytes=file_content,
        filename=filename,
        to_format=to_format,
        from_format=from_format,
    )

    # Determine output filename
    output_filename = f"converted.{to_format}"
    if "." in filename:
        base_name = filename.rsplit(".", 1)[0]
        output_filename = f"{base_name}.{to_format}"

    return Response(
        content=result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{output_filename}"',
        },
    )


@router.post("/api/v1/convert/stream", tags=["Convert"])
async def convert_stream(
    request: ConvertStreamRequest,
    auth: RequireAuth,
    service: Annotated[ConversionService, Depends(get_conversion_service)],
) -> EventSourceResponse:
    """Stream conversion with progress events.

    Requires authentication with 'convert:text' or 'admin' scope.
    Returns Server-Sent Events with progress updates and final result.
    """
    auth.require_scope("convert:text")

    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        # Starting event
        yield {
            "event": "progress",
            "data": {"stage": "starting", "progress": 0},
        }

        try:
            # Simulated progress for converting
            yield {
                "event": "progress",
                "data": {"stage": "converting", "progress": 50},
            }

            result = await service.convert_text(
                content=request.content,
                from_format=request.from_format,
                to_format=request.to_format,
            )

            yield {
                "event": "progress",
                "data": {"stage": "finalizing", "progress": 90},
            }

            # Complete event with result
            result_dict = result.to_dict()
            yield {
                "event": "complete",
                "data": {
                    "content": result_dict["content"],
                    "content_type": result.content_type,
                    "is_binary": result.is_binary,
                },
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": {"message": str(e)},
            }

    return EventSourceResponse(event_generator())
