"""Request-ID middleware.

Every request gets a unique ID that is (a) bound to all log lines produced
while handling it and (b) returned in the X-Request-ID response header.
When a user reports a bug, one ID finds every relevant log line.
"""
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import get_logger

log = get_logger("http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        structlog.contextvars.clear_contextvars()
        return response
