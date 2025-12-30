"""Format definitions and validation for Pandoc Bridge."""

import asyncio
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class FormatList:
    """Container for input and output format lists."""

    input: list[str]
    output: list[str]

    def to_dict(self) -> dict[str, list[str]]:
        """Convert to dictionary."""
        return {"input": self.input, "output": self.output}


class FormatManager:
    """Manager for Pandoc format validation and information."""

    # Common input formats
    DEFAULT_INPUT_FORMATS: list[str] = [
        "commonmark",
        "creole",
        "csv",
        "docbook",
        "docx",
        "epub",
        "fb2",
        "gfm",
        "haddock",
        "html",
        "ipynb",
        "jats",
        "json",
        "latex",
        "man",
        "markdown",
        "markdown_mmd",
        "markdown_phpextra",
        "markdown_strict",
        "mediawiki",
        "muse",
        "native",
        "odt",
        "opml",
        "org",
        "rst",
        "rtf",
        "t2t",
        "textile",
        "tikiwiki",
        "twiki",
        "vimwiki",
    ]

    # Common output formats
    DEFAULT_OUTPUT_FORMATS: list[str] = [
        "asciidoc",
        "beamer",
        "commonmark",
        "context",
        "docbook",
        "docx",
        "dokuwiki",
        "epub",
        "fb2",
        "gfm",
        "haddock",
        "html",
        "html5",
        "icml",
        "ipynb",
        "jats",
        "json",
        "latex",
        "man",
        "markdown",
        "markdown_mmd",
        "markdown_phpextra",
        "markdown_strict",
        "mediawiki",
        "ms",
        "muse",
        "native",
        "odt",
        "opendocument",
        "opml",
        "org",
        "pdf",
        "plain",
        "pptx",
        "rst",
        "rtf",
        "texinfo",
        "textile",
        "slideous",
        "slidy",
        "dzslides",
        "revealjs",
        "s5",
        "zimwiki",
    ]

    def __init__(self) -> None:
        self._input_formats: list[str] | None = None
        self._output_formats: list[str] | None = None

    async def get_formats(self) -> FormatList:
        """Get supported input and output formats from Pandoc."""
        if self._input_formats is None or self._output_formats is None:
            await self._load_formats()
        return FormatList(
            input=self._input_formats or self.DEFAULT_INPUT_FORMATS,
            output=self._output_formats or self.DEFAULT_OUTPUT_FORMATS,
        )

    async def _load_formats(self) -> None:
        """Load formats from Pandoc CLI."""
        try:
            # Get input formats
            input_proc = await asyncio.create_subprocess_exec(
                "pandoc", "--list-input-formats",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            input_stdout, _ = await input_proc.communicate()
            if input_proc.returncode == 0:
                self._input_formats = input_stdout.decode().strip().split("\n")

            # Get output formats
            output_proc = await asyncio.create_subprocess_exec(
                "pandoc", "--list-output-formats",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            output_stdout, _ = await output_proc.communicate()
            if output_proc.returncode == 0:
                self._output_formats = output_stdout.decode().strip().split("\n")

        except FileNotFoundError:
            # Pandoc not installed, use defaults
            self._input_formats = self.DEFAULT_INPUT_FORMATS
            self._output_formats = self.DEFAULT_OUTPUT_FORMATS

    def is_valid_input_format(self, format_name: str) -> bool:
        """Check if format is a valid input format."""
        formats = self._input_formats or self.DEFAULT_INPUT_FORMATS
        return format_name.lower() in formats

    def is_valid_output_format(self, format_name: str) -> bool:
        """Check if format is a valid output format."""
        formats = self._output_formats or self.DEFAULT_OUTPUT_FORMATS
        return format_name.lower() in formats

    def get_format_matrix(self) -> dict[str, list[str]]:
        """Get format conversion compatibility matrix."""
        formats = FormatList(
            input=self._input_formats or self.DEFAULT_INPUT_FORMATS,
            output=self._output_formats or self.DEFAULT_OUTPUT_FORMATS,
        )
        # In Pandoc, any input format can be converted to any output format
        return {
            input_fmt: formats.output
            for input_fmt in formats.input
        }


# Content type mappings
FORMAT_CONTENT_TYPES: dict[str, str] = {
    "html": "text/html",
    "html5": "text/html",
    "latex": "application/x-latex",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "odt": "application/vnd.oasis.opendocument.text",
    "epub": "application/epub+zip",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "markdown": "text/markdown",
    "gfm": "text/markdown",
    "commonmark": "text/markdown",
    "plain": "text/plain",
    "rst": "text/x-rst",
    "asciidoc": "text/asciidoc",
    "json": "application/json",
    "native": "application/json",
    "org": "text/org",
    "rtf": "application/rtf",
    "man": "application/x-troff-man",
    "docbook": "application/xml",
    "jats": "application/xml",
    "opml": "application/xml",
}

# Binary output formats
BINARY_FORMATS: set[str] = {"pdf", "docx", "odt", "epub", "pptx"}


def get_content_type(format_name: str) -> str:
    """Get content type for a format."""
    return FORMAT_CONTENT_TYPES.get(format_name.lower(), "application/octet-stream")


def is_binary_format(format_name: str) -> bool:
    """Check if format produces binary output."""
    return format_name.lower() in BINARY_FORMATS


@lru_cache
def get_format_manager() -> FormatManager:
    """Get cached format manager instance."""
    return FormatManager()
