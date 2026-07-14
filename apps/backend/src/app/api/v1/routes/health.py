"""Health endpoints.

/health       — liveness: "is the process up?"
/health/ready — readiness: "can it serve traffic?" (DB/Redis/Chroma checks
                will be added in Milestone 1+ as those services come online)
"""
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@router.get("/health/ready")
async def ready() -> dict:
    # M1+: ping Postgres, Redis and Chroma here and report each dependency.
    return {"status": "ready", "checks": {}}
