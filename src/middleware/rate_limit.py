"""Rate limiting middleware."""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(
        self,
        app: Callable,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Clean old requests
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip] if ts > window_start
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return True

        # Check burst (requests in last second)
        last_second = now - 1
        recent = sum(1 for ts in self.requests[client_ip] if ts > last_second)
        if recent >= self.burst_size:
            return True

        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        if self._is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please slow down.",
                        "details": {"retry_after_seconds": 60},
                    }
                },
                headers={"Retry-After": "60"},
            )

        # Record request
        self.requests[client_ip].append(time.time())

        return await call_next(request)
