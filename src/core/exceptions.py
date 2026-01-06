"""Custom exceptions for Pandoc Bridge."""

from typing import Any


class PandocBridgeError(Exception):
    """Base exception for Pandoc Bridge."""

    code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class FormatNotSupportedError(PandocBridgeError):
    """Raised when a format is not supported."""

    code = "FORMAT_NOT_SUPPORTED"
    http_status = 400

    def __init__(
        self,
        format_name: str,
        format_type: str = "input/output",
        supported_formats: list[str] | None = None,
    ) -> None:
        message = f"Format '{format_name}' is not supported as {format_type}"
        details: dict[str, Any] = {"format": format_name, "format_type": format_type}
        if supported_formats:
            details["supported_formats"] = supported_formats
        super().__init__(message, details)


class ConversionError(PandocBridgeError):
    """Raised when document conversion fails."""

    code = "CONVERSION_FAILED"
    http_status = 422

    def __init__(
        self,
        message: str,
        from_format: str | None = None,
        to_format: str | None = None,
        pandoc_error: str | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if from_format:
            details["from_format"] = from_format
        if to_format:
            details["to_format"] = to_format
        if pandoc_error:
            details["pandoc_error"] = pandoc_error
        super().__init__(message, details)


class ConversionTimeoutError(PandocBridgeError):
    """Raised when conversion times out."""

    code = "TIMEOUT"
    http_status = 504

    def __init__(self, timeout_seconds: int) -> None:
        message = f"Conversion timed out after {timeout_seconds} seconds"
        super().__init__(message, {"timeout_seconds": timeout_seconds})


class AuthenticationError(PandocBridgeError):
    """Raised when authentication fails."""

    code = "UNAUTHORIZED"
    http_status = 401

    def __init__(
        self, message: str = "Invalid or missing authentication token"
    ) -> None:
        super().__init__(message)


class AuthorizationError(PandocBridgeError):
    """Raised when authorization fails."""

    code = "FORBIDDEN"
    http_status = 403

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_scopes: list[str] | None = None,
    ) -> None:
        details = {}
        if required_scopes:
            details["required_scopes"] = required_scopes
        super().__init__(message, details)


class FileSizeError(PandocBridgeError):
    """Raised when file size exceeds limit."""

    code = "FILE_TOO_LARGE"
    http_status = 413

    def __init__(self, file_size: int, max_size: int) -> None:
        message = (
            f"File size ({file_size} bytes) exceeds maximum allowed ({max_size} bytes)"
        )
        super().__init__(message, {"file_size": file_size, "max_size": max_size})
