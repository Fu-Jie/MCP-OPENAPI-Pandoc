# Pandoc Bridge

[![CI/CD Pipeline](https://github.com/Fu-Jie/MCP-OPENAPI-Pandoc/actions/workflows/pipeline.yml/badge.svg)](https://github.com/Fu-Jie/MCP-OPENAPI-Pandoc/actions/workflows/pipeline.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

A document format conversion service using Pandoc, supporting both REST (OpenAPI 3.1) and MCP (Model Context Protocol) interfaces.

## Features

- **40+ Format Support**: Convert between Markdown, HTML, LaTeX, DOCX, PDF, and many more formats
- **Dual Protocol**: REST API with OpenAPI documentation and MCP server for AI assistants
- **Bearer Token Auth**: Shared JWT authentication across both protocols
- **Streaming Support**: Server-Sent Events for progress tracking
- **Rate Limiting**: Built-in protection against abuse
- **Docker Ready**: Production-ready containerization with multi-arch support

## Documentation

- [API Reference](docs/API.md) - Detailed REST API documentation
- [MCP Integration](docs/MCP.md) - Model Context Protocol guide
- [Container Registry Guide](docs/CONTAINER_REGISTRY.md) - Docker deployment guide
- [OpenAPI Spec](/docs) - Interactive Swagger UI (when running)

## Quick Start

### Using Docker Compose

```bash
# Start the service
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server
uvicorn src.main:app --reload

# Or use the CLI
pandoc-bridge
```

## API Endpoints

### Public Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Service information |
| `GET /health` | Health check with Pandoc version |
| `GET /api/v1/formats` | List supported formats |
| `GET /docs` | Swagger UI documentation |

### Protected Endpoints (Require Bearer Token)

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/convert/text` | Convert text content |
| `POST /api/v1/convert/file` | Convert uploaded file |
| `POST /api/v1/convert/stream` | Stream conversion with SSE |

### MCP Endpoint

| Endpoint | Description |
|----------|-------------|
| `POST /mcp` | MCP Streamable HTTP transport |

## Usage Examples

### Convert Text (REST)

```bash
# Get a token (for development, tokens are pre-configured)
TOKEN="your-jwt-token"

# Convert Markdown to HTML
curl -X POST http://localhost:8000/api/v1/convert/text \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Hello World\n\nThis is **bold** text.",
    "from_format": "markdown",
    "to_format": "html"
  }'
```

### Convert File (REST)

```bash
curl -X POST http://localhost:8000/api/v1/convert/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.md" \
  -F "to_format=docx" \
  -o converted.docx
```

### Using with Claude Desktop (MCP)

Add to your Claude Desktop configuration:

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

Or with authentication:

```json
{
  "mcpServers": {
    "pandoc-bridge": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "--header", "Authorization: Bearer ${PANDOC_TOKEN}",
        "http://localhost:8000/mcp"
      ]
    }
  }
}
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `convert_text` | Convert text between formats |
| `convert_file_base64` | Convert base64-encoded files |
| `list_formats` | Get supported formats |
| `get_service_info` | Get version information |

## MCP Resources

| Resource | Description |
|----------|-------------|
| `formats://list` | JSON list of supported formats |
| `formats://matrix` | Format conversion compatibility matrix |

## Authentication

### Scopes

| Scope | Description |
|-------|-------------|
| `formats:read` | Query formats (public) |
| `convert:text` | Text conversion |
| `convert:file` | File conversion |
| `admin` | Full access |

### Token Format

```python
{
    "sub": "client-id",
    "scopes": ["formats:read", "convert:text", "convert:file"],
    "exp": 1735600000,
    "iat": 1735513600
}
```

## Configuration

Environment variables (see [.env.example](.env.example)):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENVIRONMENT` | `development` | Environment (development/production) |
| `JWT_SECRET_KEY` | *(required in prod)* | JWT signing key (min 32 chars) |
| `JWT_EXPIRE_HOURS` | `24` | Token expiration time |
| `MAX_FILE_SIZE_MB` | `50` | Maximum file size |
| `CONVERSION_TIMEOUT` | `60` | Conversion timeout in seconds |

> ⚠️ **Security Note**: Always set `JWT_SECRET_KEY` in production. Generate one with:
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(32))"
> ```

## Development

### Run Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Lint Code

```bash
# Run ruff
ruff check src tests
ruff format src tests
```

### Type Check

```bash
mypy src
```

### Security Scan

```bash
# Install security tools
pip install bandit safety

# Run security scan
bandit -r src -ll

# Check dependencies
safety check
```

## CI/CD

The project uses GitHub Actions for continuous integration and deployment:

- **CI Pipeline** (`pipeline.yml`):
  - Runs on Python 3.12 and 3.13
  - Linting with ruff
  - Type checking with mypy
  - Tests with pytest and coverage
  - Security scanning with bandit
  - Deploys documentation to GitHub Pages

- **Container Publishing** (`publish-container.yml`):
  - Triggered on version tags (`v*.*.*`)
  - Multi-arch builds (amd64, arm64)
  - Publishes to GitHub Container Registry

### Running Locally

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
vim .env

# Start with Docker
docker-compose up --build
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                       │
│                   (Port 8000)                        │
├─────────────────────┬───────────────────────────────┤
│   REST API          │         MCP Server            │
│   /api/v1/*         │         /mcp                  │
│   (OpenAPI 3.1)     │    (Streamable HTTP)          │
├─────────────────────┴───────────────────────────────┤
│              Shared Auth (Bearer Token)              │
├─────────────────────────────────────────────────────┤
│              ConversionService (Core)                │
├─────────────────────────────────────────────────────┤
│                    Pandoc CLI                        │
└─────────────────────────────────────────────────────┘
```

## License

MIT License - see [LICENSE](LICENSE) for details.
