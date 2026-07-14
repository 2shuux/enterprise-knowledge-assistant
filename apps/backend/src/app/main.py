"""Application factory.

Building the app inside a function (instead of at import time) makes it
trivial to create fresh, isolated app instances in tests with different
settings — a pattern you'll appreciate from Milestone 1 onwards.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, json_logs=settings.is_production)
    log = get_logger("startup")

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/api/docs",          # Swagger UI
        openapi_url="/api/openapi.json",
    )

    # In dev the Vite server (5173) calls the API (8000) cross-origin.
    # In production Nginx serves both from one origin, so this list stays tight.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    log.info("app_configured", env=settings.app_env)
    return app


app = create_app()
