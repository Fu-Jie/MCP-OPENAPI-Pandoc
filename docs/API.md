# Pandoc Bridge API Documentation

## Overview

Pandoc Bridge provides a REST API for document format conversion using Pandoc. The API follows OpenAPI 3.1 specification and supports JWT Bearer token authentication.

Base URL: `http://localhost:8000`

## Authentication

Protected endpoints require an API Key in the `Authorization` header:

```
Authorization: Bearer sk-your-api-key
```

### API Key Configuration

Set API keys via environment variable:

```bash
# Single key (no expiry)
API_KEYS=sk-abc123xyz

# Single key with expiry
API_KEYS=sk-abc123xyz:2025-12-31

# Multiple keys
API_KEYS=sk-key1:2025-12-31,sk-key2:2026-06-30,sk-key3
```

### Generate API Key

```bash
python -c "import secrets; print(f'sk-{secrets.token_urlsafe(24)}')"
```

### Expiry Format

Use ISO date format: `YYYY-MM-DD`

When an API key expires, requests will receive:
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "API key expired on 2025-12-31"
  }
}
```

### Scopes

API keys have full admin access to all endpoints.

---

## Endpoints

### Public Endpoints

#### GET /
Get service information.

**Response 200:**
```json
{
  "name": "pandoc-bridge",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "formats": "/api/v1/formats",
    "convert_text": "/api/v1/convert/text",
    "convert_file": "/api/v1/convert/file",
    "convert_stream": "/api/v1/convert/stream",
    "mcp": "/mcp",
    "docs": "/docs"
  }
}
```

#### GET /health
Health check endpoint.

**Response 200:**
```json
{
  "status": "healthy",
  "pandoc_version": "pandoc 3.1.11",
  "timestamp": "2025-01-06T10:30:00Z"
}
```

#### GET /api/v1/formats
List supported input and output formats.

**Response 200:**
```json
{
  "input": ["markdown", "html", "latex", "docx", "..."],
  "output": ["markdown", "html", "latex", "pdf", "docx", "..."]
}
```

---

### Protected Endpoints

#### POST /api/v1/convert/text
Convert text content between formats.

**Required Scope:** `convert:text` or `admin`

**Request Body:**
```json
{
  "content": "# Hello World\n\nThis is **bold** text.",
  "from_format": "markdown",
  "to_format": "html",
  "options": {
    "standalone": true,
    "table_of_contents": false,
    "number_sections": false,
    "wrap": "auto",
    "columns": 80,
    "pdf_engine": null
  }
}
```

**Options:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `standalone` | boolean | true | Generate standalone document |
| `table_of_contents` | boolean | false | Include table of contents |
| `number_sections` | boolean | false | Number section headings |
| `wrap` | string | "auto" | Text wrapping: auto, none, preserve |
| `columns` | integer | 80 | Column width for wrapping |
| `pdf_engine` | string | null | PDF engine: pdflatex, xelatex, lualatex |

> **Note:** For Chinese/Japanese/Korean PDF output, use `"pdf_engine": "xelatex"`
```

**Response 200:**
```json
{
  "content": "<!DOCTYPE html>...<h1>Hello World</h1>...",
  "content_type": "text/html",
  "is_binary": false
}
```

**Error Responses:**
- `400` - Format not supported
- `401` - Unauthorized
- `403` - Forbidden (missing scope)
- `422` - Conversion failed
- `429` - Rate limited
- `504` - Conversion timeout

---

#### POST /api/v1/convert/file
Convert an uploaded file.

**Required Scope:** `convert:file` or `admin`

**Request:** `multipart/form-data`
- `file` (required): File to convert
- `to_format` (required): Target format
- `from_format` (optional): Source format (auto-detected if omitted)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/convert/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.md" \
  -F "to_format=docx" \
  -o converted.docx
```

**Response 200:** Binary file download

**Error Responses:**
- `400` - Format not supported
- `401` - Unauthorized
- `403` - Forbidden
- `413` - File too large
- `422` - Conversion failed

---

#### POST /api/v1/convert/stream
Stream conversion with Server-Sent Events (SSE).

**Required Scope:** `convert:text` or `admin`

**Request Body:**
```json
{
  "content": "# Document\n\nContent here...",
  "from_format": "markdown",
  "to_format": "html"
}
```

**Response:** `text/event-stream`

```
event: progress
data: {"stage": "starting", "progress": 0}

event: progress
data: {"stage": "converting", "progress": 50}

event: progress
data: {"stage": "finalizing", "progress": 90}

event: complete
data: {"content": "...", "content_type": "text/html", "is_binary": false}
```

**Error Event:**
```
event: error
data: {"message": "Conversion failed: ..."}
```

---

#### POST /api/v1/convert/batch
Convert multiple documents in a single request.

**Required Scope:** `convert:text` or `admin`

**Request Body:**
```json
{
  "items": [
    {
      "id": "doc1",
      "content": "# First Document",
      "from_format": "markdown",
      "to_format": "html"
    },
    {
      "id": "doc2", 
      "content": "# Second Document",
      "from_format": "markdown",
      "to_format": "latex",
      "options": {"standalone": false}
    }
  ]
}
```

**Limits:** Maximum 20 items per batch.

**Response 200:**
```json
{
  "results": [
    {
      "id": "doc1",
      "success": true,
      "content": "<!DOCTYPE html>...",
      "content_type": "text/html",
      "is_binary": false
    },
    {
      "id": "doc2",
      "success": true,
      "content": "\\section{Second Document}...",
      "content_type": "application/x-latex",
      "is_binary": false
    }
  ],
  "total": 2,
  "succeeded": 2,
  "failed": 0
}
```

---

## Request Tracing

All requests include tracing headers for debugging:

**Request Header (optional):**
```
X-Trace-ID: your-custom-trace-id
```

**Response Headers:**
```
X-Trace-ID: abc12345
X-Response-Time: 125.50ms
```

If no `X-Trace-ID` is provided in the request, a random one is generated.

---

## Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {
      "additional": "context"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `FORMAT_NOT_SUPPORTED` | 400 | Invalid input/output format |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `FILE_TOO_LARGE` | 413 | File exceeds size limit |
| `CONVERSION_FAILED` | 422 | Pandoc conversion error |
| `RATE_LIMITED` | 429 | Too many requests |
| `TIMEOUT` | 504 | Conversion timed out |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Rate Limiting

The API enforces rate limiting:
- **60 requests per minute** per IP
- **10 requests per second** burst limit

Rate limited responses include:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please slow down.",
    "details": {"retry_after_seconds": 60}
  }
}
```

---

## Supported Formats

### Common Input Formats
- `markdown`, `gfm`, `commonmark` - Markdown variants
- `html` - HTML
- `latex` - LaTeX
- `docx` - Microsoft Word
- `odt` - OpenDocument Text
- `rst` - reStructuredText
- `org` - Org mode
- `ipynb` - Jupyter Notebook

### Common Output Formats
- `html`, `html5` - HTML
- `pdf` - PDF (requires LaTeX)
- `docx` - Microsoft Word
- `odt` - OpenDocument Text
- `latex` - LaTeX
- `epub` - EPUB ebook
- `pptx` - PowerPoint
- `plain` - Plain text

For a complete list, call `GET /api/v1/formats`.

---

## Code Examples

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"
TOKEN = "your-jwt-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Convert text
response = requests.post(
    f"{BASE_URL}/api/v1/convert/text",
    headers=headers,
    json={
        "content": "# Hello\n\nWorld",
        "from_format": "markdown",
        "to_format": "html"
    }
)
print(response.json()["content"])
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8000";
const TOKEN = "your-jwt-token";

const response = await fetch(`${BASE_URL}/api/v1/convert/text`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${TOKEN}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    content: "# Hello\n\nWorld",
    from_format: "markdown",
    to_format: "html"
  })
});

const data = await response.json();
console.log(data.content);
```

### cURL

```bash
# Convert markdown to HTML
curl -X POST http://localhost:8000/api/v1/convert/text \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "# Hello", "from_format": "markdown", "to_format": "html"}'

# Convert file
curl -X POST http://localhost:8000/api/v1/convert/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@input.md" \
  -F "to_format=pdf" \
  -o output.pdf
```

---

## OpenAPI Specification

The full OpenAPI 3.1 specification is available at:
- Interactive docs: `GET /docs` (Swagger UI)
- ReDoc: `GET /redoc`
- JSON spec: `GET /openapi.json`
