"""Pydantic schemas for REST API."""

from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    """Service information response."""

    name: str
    version: str
    endpoints: dict[str, str]


class HealthCheck(BaseModel):
    """Health check response."""

    status: str
    pandoc_version: str
    timestamp: str


class FormatListResponse(BaseModel):
    """Format list response."""

    input: list[str]
    output: list[str]


class ConversionOptions(BaseModel):
    """Optional conversion settings."""

    standalone: bool = Field(default=True, description="Generate standalone document")
    table_of_contents: bool = Field(
        default=False, description="Include table of contents"
    )
    number_sections: bool = Field(default=False, description="Number section headings")
    wrap: str = Field(
        default="auto", description="Text wrapping mode: auto, none, preserve"
    )
    columns: int = Field(default=80, description="Column width for wrapping")
    pdf_engine: str | None = Field(
        default=None, 
        description="PDF engine: pdflatex, xelatex, lualatex (xelatex recommended for CJK)"
    )


class ConvertTextRequest(BaseModel):
    """Request for text conversion."""

    content: str = Field(..., description="Text content to convert")
    from_format: str = Field(..., description="Source format (e.g., 'markdown')")
    to_format: str = Field(..., description="Target format (e.g., 'html')")
    options: ConversionOptions | None = Field(
        default=None, description="Conversion options"
    )


class ConvertTextResponse(BaseModel):
    """Response for text conversion."""

    content: str = Field(..., description="Converted content (base64 if binary)")
    content_type: str = Field(..., description="MIME type of the output")
    is_binary: bool = Field(..., description="Whether content is base64-encoded binary")


class ConvertStreamRequest(BaseModel):
    """Request for streaming conversion."""

    content: str = Field(..., description="Text content to convert")
    from_format: str = Field(..., description="Source format")
    to_format: str = Field(..., description="Target format")


class StreamEvent(BaseModel):
    """Server-Sent Event data."""

    event: str
    data: dict[str, str | int | bool | float | None]


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: dict[str, str | int | bool | list[str] | None] = Field(
        default_factory=dict
    )


class ErrorResponse(BaseModel):
    """Error response wrapper."""

    error: ErrorDetail


class BatchConvertItem(BaseModel):
    """Single item in batch conversion request."""

    id: str = Field(..., description="Unique identifier for this item")
    content: str = Field(..., description="Text content to convert")
    from_format: str = Field(..., description="Source format")
    to_format: str = Field(..., description="Target format")
    options: ConversionOptions | None = Field(default=None, description="Conversion options")


class BatchConvertRequest(BaseModel):
    """Request for batch conversion."""

    items: list[BatchConvertItem] = Field(..., description="List of items to convert", max_length=20)


class BatchConvertResultItem(BaseModel):
    """Single result in batch conversion response."""

    id: str = Field(..., description="Item identifier from request")
    success: bool = Field(..., description="Whether conversion succeeded")
    content: str | None = Field(default=None, description="Converted content if successful")
    content_type: str | None = Field(default=None, description="MIME type if successful")
    is_binary: bool = Field(default=False, description="Whether content is base64-encoded")
    error: str | None = Field(default=None, description="Error message if failed")


class BatchConvertResponse(BaseModel):
    """Response for batch conversion."""

    results: list[BatchConvertResultItem] = Field(..., description="Conversion results")
    total: int = Field(..., description="Total items processed")
    succeeded: int = Field(..., description="Number of successful conversions")
    failed: int = Field(..., description="Number of failed conversions")
