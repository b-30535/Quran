from fastapi import APIRouter

from app.core.database import database_is_connected

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Check API liveness")
async def health() -> dict[str, str]:
    """Liveness check; contains no secrets or infrastructure details."""
    return {"status": "ok", "service": "noor-al-quran-api"}


@router.get("/ready", summary="Check service readiness")
async def ready() -> dict[str, str | bool]:
    """Reports whether MongoDB-backed features can be served."""
    connected = database_is_connected()
    return {
        "status": "ready" if connected else "degraded",
        "database_connected": connected,
    }
