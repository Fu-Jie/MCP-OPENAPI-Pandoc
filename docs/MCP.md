# MCP (Model Context Protocol) Integration

Pandoc Bridge provides an MCP server for integration with AI assistants like Claude Desktop.

## Endpoint

The MCP server is available at: `POST /mcp`

It uses the Streamable HTTP transport provided by FastMCP.

## Available Tools

### convert_text

Convert text content between document formats.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | string | Yes | Text content to convert |
| `from_format` | string | Yes | Source format (e.g., 'markdown') |
| `to_format` | string | Yes | Target format (e.g., 'html') |
| `standalone` | boolean | No | Generate standalone document (default: true) |
| `pdf_engine` | string | No | PDF engine: pdflatex, xelatex (for CJK), lualatex |

**Example:**
```json
{
  "content": "# Hello World\n\nThis is **bold**.",
  "from_format": "markdown",
  "to_format": "html",
  "standalone": true
}
```

**Example with CJK PDF:**
```json
{
  "content": "# 你好世界\n\n这是中文内容。",
  "from_format": "markdown",
  "to_format": "pdf",
  "pdf_engine": "xelatex"
}
```

**Response:**
```json
{
  "success": true,
  "content": "<!DOCTYPE html>...",
  "content_type": "text/html",
  "is_binary": false
}
```

---

### convert_file_base64

Convert a base64-encoded file to another format.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_base64` | string | Yes | Base64-encoded file content |
| `filename` | string | Yes | Original filename (for format detection) |
| `to_format` | string | Yes | Target format |
| `pdf_engine` | string | No | PDF engine for PDF output (xelatex for CJK) |

**Example:**
```json
{
  "file_base64": "IyBIZWxsbyBXb3JsZAo=",
  "filename": "document.md",
  "to_format": "html"
}
```

**Response:**
```json
{
  "success": true,
  "content_base64": "PCFET0NUWVBFIGh0bWw+Li4u",
  "content_type": "text/html"
}
```

---

### list_formats

Get list of supported input and output formats.

**Parameters:** None

**Response:**
```json
{
  "input": ["markdown", "html", "latex", "docx", "..."],
  "output": ["markdown", "html", "pdf", "docx", "..."]
}
```

---

### get_service_info

Get service and Pandoc version information.

**Parameters:** None

**Response:**
```json
{
  "service_version": "1.0.0",
  "pandoc_version": "pandoc 3.1.11"
}
```

---

## Available Resources

### formats://list

JSON list of all supported formats.

### formats://matrix

Format conversion compatibility matrix showing which input formats can convert to which output formats.

---

## Claude Desktop Configuration

### Basic Setup (No Auth)

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "pandoc-bridge": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8000/mcp"]
    }
  }
}
```

### With Authentication

```json
{
  "mcpServers": {
    "pandoc-bridge": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "--header", "Authorization: Bearer ${PANDOC_TOKEN}",
        "http://localhost:8000/mcp"
      ],
      "env": {
        "PANDOC_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

### Remote Server

For a remote deployment:

```json
{
  "mcpServers": {
    "pandoc-bridge": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "--header", "Authorization: Bearer ${PANDOC_TOKEN}",
        "https://your-server.com/mcp"
      ],
      "env": {
        "PANDOC_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

---

## Usage Examples with Claude

Once configured, you can ask Claude to:

- "Convert this markdown to HTML: # Hello World"
- "What document formats does Pandoc support?"
- "Convert this LaTeX equation to HTML: $E = mc^2$"
- "Transform this RST documentation to Markdown"

Claude will use the appropriate MCP tools automatically.

---

## Programmatic Access

### Python Example

```python
import httpx
import json

async def call_mcp_tool(tool_name: str, arguments: dict):
    """Call an MCP tool via HTTP."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": 1
            },
            headers={"Content-Type": "application/json"}
        )
        return response.json()

# Example usage
result = await call_mcp_tool("convert_text", {
    "content": "# Hello",
    "from_format": "markdown", 
    "to_format": "html"
})
print(result)
```

---

## Troubleshooting

### Connection Refused

Ensure the server is running:
```bash
curl http://localhost:8000/health
```

### Authentication Errors

Verify your token is valid:
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/formats
```

### Format Not Supported

Check available formats:
```bash
curl http://localhost:8000/api/v1/formats | jq
```

### Timeout Issues

For large documents, increase the timeout in your configuration or use streaming endpoints.
