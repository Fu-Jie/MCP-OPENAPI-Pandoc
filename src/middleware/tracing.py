"""Request tracing middleware."""

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request tracing with unique trace IDs."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        """Process request with tracing."""
        # Generate or extract trace ID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id

        # Record start time
        start_time = time.perf_counter()

        # Log request
        logger.info(
            "[%s] %s %s started",
            trace_id,
            request.method,
            request.url.path,
        )

        # Process request
        response: Response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add trace headers to response
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log response
        logger.info(
            "[%s] %s %s completed - %d (%.2fms)",
            trace_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
