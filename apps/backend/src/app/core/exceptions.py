"""Domain exceptions + global handlers.

Services raise *domain* exceptions (they know nothing about HTTP).
This module maps them to RFC 7807 "problem details" JSON responses in ONE
place, so route handlers never need try/except boilerplate.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

log = get_logger("exceptions")


class AppError(Exception):
    """Base class for all domain errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "Something went wrong"):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"


def _problem(request: Request, status_code: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "type": "about:blank",
            "title": code,
            "status": status_code,
            "detail": detail,
            "instance": str(request.url.path),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        log.warning("domain_error", code=exc.code, detail=exc.message, path=request.url.path)
        return _problem(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Never leak stack traces to clients; log them instead.
        log.exception("unhandled_error", path=request.url.path)
        return _problem(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            "Internal server error",
        )
