"""Main application entry point - FastAPI + FastMCP integration."""

import logging
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.config import get_settings
from src.core.exceptions import PandocBridgeError
from src.mcp.server import mcp
from src.middleware import RateLimitMiddleware, TracingMiddleware

settings = get_settings()

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Pandoc Bridge",
    description="""
    Document format conversion service using Pandoc.
    
    Supports both REST API (OpenAPI 3.1) and MCP (Model Context Protocol) interfaces.
    
    ## Features
    
    - Convert text between 40+ document formats
    - Upload and convert files
    - Streaming conversion with progress events
    - Bearer token authentication
    
    ## Authentication
    
    Protected endpoints require a Bearer token in the Authorization header:
    ```
    Authorization: Bearer <token>
    ```
    
    ## MCP Server
    
    The MCP server is available at `/mcp` endpoint for Claude Desktop and other MCP clients.
    """,
    version=settings.service_version,
    openapi_tags=[
        {"name": "Info", "description": "Service information and health checks"},
        {"name": "Formats", "description": "Format listing and validation"},
        {"name": "Convert", "description": "Document conversion operations"},
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tracing middleware (must be before rate limiting)
app.add_middleware(TracingMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=60, burst_size=10)


# Exception handlers
@app.exception_handler(PandocBridgeError)
async def pandoc_bridge_exception_handler(
    request: Request, exc: PandocBridgeError
) -> JSONResponse:
    """Handle custom exceptions."""
    logger.warning("Request error: %s - %s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict(),
    )


# Include REST routes
app.include_router(router)

# Mount MCP server
# FastMCP provides HTTP transport for MCP
app.mount("/mcp", mcp.http_app())


def run() -> None:
    """Run the application with uvicorn."""
    logger.info("Starting Pandoc Bridge on %s:%d", settings.host, settings.port)
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    run()
