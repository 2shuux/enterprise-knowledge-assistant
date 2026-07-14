"""Structured JSON logging via structlog.

Why JSON logs? In production, logs are read by machines (Datadog, CloudWatch,
grep + jq) far more often than by humans. One JSON object per line with a
request_id lets you trace a single request across the whole system.
In development we render pretty, colored console output instead.
"""
import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO", *, json_logs: bool = False) -> None:
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,  # picks up request_id set by middleware
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    renderer = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(stream=sys.stdout, level=log_level.upper(), format="%(message)s")


def get_logger(name: str = "app"):
    return structlog.get_logger(name)
