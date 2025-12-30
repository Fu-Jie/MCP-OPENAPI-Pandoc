"""Pandoc conversion service."""

import asyncio
import base64
import builtins
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.config import get_settings
from src.core.exceptions import ConversionError, FormatNotSupportedError, TimeoutError
from src.core.formats import (
    FormatList,
    FormatManager,
    get_content_type,
    get_format_manager,
    is_binary_format,
)


@dataclass
class ConversionOptions:
    """Options for document conversion."""

    standalone: bool = True
    table_of_contents: bool = False
    number_sections: bool = False
    wrap: str = "auto"  # auto, none, preserve
    columns: int = 80
    extra_args: list[str] = field(default_factory=list)


@dataclass
class ConversionResult:
    """Result of a conversion operation."""

    content: bytes
    content_type: str
    is_binary: bool
    from_format: str
    to_format: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        if self.is_binary:
            content_value = base64.b64encode(self.content).decode("utf-8")
        else:
            content_value = self.content.decode("utf-8")

        return {
            "content": content_value,
            "content_type": self.content_type,
            "is_binary": self.is_binary,
            "from_format": self.from_format,
            "to_format": self.to_format,
        }


class ConversionService:
    """Service for converting documents using Pandoc."""

    def __init__(self, format_manager: FormatManager | None = None) -> None:
        self.format_manager = format_manager or get_format_manager()
        self.settings = get_settings()

    async def convert_text(
        self,
        content: str,
        from_format: str,
        to_format: str,
        options: ConversionOptions | None = None,
    ) -> ConversionResult:
        """Convert text content from one format to another.

        Args:
            content: The text content to convert
            from_format: Source format (e.g., 'markdown')
            to_format: Target format (e.g., 'html')
            options: Optional conversion options

        Returns:
            ConversionResult with the converted content
        """
        options = options or ConversionOptions()

        # Validate formats
        await self._validate_formats(from_format, to_format)

        # Build pandoc command
        cmd = self._build_command(from_format, to_format, options)

        # Execute conversion
        output = await self._execute_pandoc(
            cmd,
            input_data=content.encode("utf-8"),
            from_format=from_format,
            to_format=to_format,
        )

        return ConversionResult(
            content=output,
            content_type=get_content_type(to_format),
            is_binary=is_binary_format(to_format),
            from_format=from_format,
            to_format=to_format,
        )

    async def convert_file(
        self,
        file_bytes: bytes,
        filename: str,
        to_format: str,
        from_format: str | None = None,
        options: ConversionOptions | None = None,
    ) -> ConversionResult:
        """Convert a file from one format to another.

        Args:
            file_bytes: The file content as bytes
            filename: Original filename (used to detect format)
            to_format: Target format
            from_format: Source format (optional, detected from extension if not provided)
            options: Optional conversion options

        Returns:
            ConversionResult with the converted content
        """
        options = options or ConversionOptions()

        # Detect source format from filename if not provided
        if from_format is None:
            from_format = self._detect_format(filename)

        # Validate formats
        await self._validate_formats(from_format, to_format)

        # Use temporary files for binary formats
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / filename
            output_ext = self._get_extension(to_format)
            output_path = Path(tmpdir) / f"output.{output_ext}"

            # Write input file
            input_path.write_bytes(file_bytes)

            # Build command with file paths
            cmd = self._build_command(
                from_format,
                to_format,
                options,
                input_file=str(input_path),
                output_file=str(output_path),
            )

            # Execute conversion
            await self._execute_pandoc(
                cmd,
                from_format=from_format,
                to_format=to_format,
            )

            # Read output
            if output_path.exists():
                output = output_path.read_bytes()
            else:
                raise ConversionError(
                    "Output file was not created",
                    from_format=from_format,
                    to_format=to_format,
                )

        return ConversionResult(
            content=output,
            content_type=get_content_type(to_format),
            is_binary=is_binary_format(to_format),
            from_format=from_format,
            to_format=to_format,
        )

    async def convert_file_base64(
        self,
        file_base64: str,
        filename: str,
        to_format: str,
        from_format: str | None = None,
        options: ConversionOptions | None = None,
    ) -> ConversionResult:
        """Convert a base64-encoded file.

        Args:
            file_base64: Base64-encoded file content
            filename: Original filename
            to_format: Target format
            from_format: Source format (optional)
            options: Conversion options

        Returns:
            ConversionResult with converted content
        """
        try:
            file_bytes = base64.b64decode(file_base64)
        except Exception as e:
            raise ConversionError(f"Invalid base64 encoding: {e}") from e

        return await self.convert_file(
            file_bytes=file_bytes,
            filename=filename,
            to_format=to_format,
            from_format=from_format,
            options=options,
        )

    async def get_formats(self) -> FormatList:
        """Get supported input and output formats."""
        return await self.format_manager.get_formats()

    async def get_pandoc_version(self) -> str:
        """Get Pandoc version string."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "pandoc",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                # First line contains version
                first_line = stdout.decode().strip().split("\n")[0]
                return first_line
            return "unknown"
        except FileNotFoundError:
            return "not installed"

    async def _validate_formats(self, from_format: str, to_format: str) -> None:
        """Validate that formats are supported."""
        formats = await self.format_manager.get_formats()

        if from_format.lower() not in formats.input:
            raise FormatNotSupportedError(
                from_format,
                format_type="input",
                supported_formats=formats.input[:10],  # Show first 10
            )

        if to_format.lower() not in formats.output:
            raise FormatNotSupportedError(
                to_format,
                format_type="output",
                supported_formats=formats.output[:10],
            )

    def _build_command(
        self,
        from_format: str,
        to_format: str,
        options: ConversionOptions,
        input_file: str | None = None,
        output_file: str | None = None,
    ) -> list[str]:
        """Build pandoc command line arguments."""
        cmd = ["pandoc", "-f", from_format, "-t", to_format]

        if options.standalone:
            cmd.append("--standalone")

        if options.table_of_contents:
            cmd.append("--toc")

        if options.number_sections:
            cmd.append("--number-sections")

        if options.wrap != "auto":
            cmd.extend(["--wrap", options.wrap])

        cmd.extend(["--columns", str(options.columns)])

        if options.extra_args:
            cmd.extend(options.extra_args)

        if input_file:
            cmd.append(input_file)

        if output_file:
            cmd.extend(["-o", output_file])

        return cmd

    async def _execute_pandoc(
        self,
        cmd: list[str],
        input_data: bytes | None = None,
        from_format: str = "",
        to_format: str = "",
    ) -> bytes:
        """Execute pandoc command and return output."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=input_data),
                    timeout=self.settings.conversion_timeout,
                )
            except builtins.TimeoutError as e:
                proc.kill()
                await proc.wait()
                raise TimeoutError(self.settings.conversion_timeout) from e

            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                raise ConversionError(
                    f"Pandoc conversion failed: {error_msg}",
                    from_format=from_format,
                    to_format=to_format,
                    pandoc_error=error_msg,
                )

            return stdout

        except FileNotFoundError as e:
            raise ConversionError(
                "Pandoc is not installed or not found in PATH",
                from_format=from_format,
                to_format=to_format,
            ) from e

    def _detect_format(self, filename: str) -> str:
        """Detect format from filename extension."""
        ext_to_format: dict[str, str] = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".html": "html",
            ".htm": "html",
            ".tex": "latex",
            ".latex": "latex",
            ".docx": "docx",
            ".odt": "odt",
            ".epub": "epub",
            ".rst": "rst",
            ".txt": "plain",
            ".json": "json",
            ".xml": "docbook",
            ".org": "org",
            ".rtf": "rtf",
            ".ipynb": "ipynb",
        }
        suffix = Path(filename).suffix.lower()
        format_name = ext_to_format.get(suffix)
        if format_name is None:
            raise FormatNotSupportedError(
                suffix,
                format_type="input (file extension)",
            )
        return format_name

    def _get_extension(self, format_name: str) -> str:
        """Get file extension for a format."""
        format_to_ext: dict[str, str] = {
            "markdown": "md",
            "gfm": "md",
            "commonmark": "md",
            "html": "html",
            "html5": "html",
            "latex": "tex",
            "pdf": "pdf",
            "docx": "docx",
            "odt": "odt",
            "epub": "epub",
            "pptx": "pptx",
            "rst": "rst",
            "plain": "txt",
            "json": "json",
            "native": "hs",
            "org": "org",
            "rtf": "rtf",
            "asciidoc": "adoc",
            "man": "1",
        }
        return format_to_ext.get(format_name.lower(), format_name)
