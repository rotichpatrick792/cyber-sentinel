from fastapi import APIRouter

# Top-level router for API version 1.
# Feature-specific routers (health, predict, alerts, ...) will be
# included here as the project grows.
api_router = APIRouter(tags=["v1"])


@api_router.get("/ping", summary="Ping the v1 API")
async def ping() -> dict:
    """Simple liveness check for the versioned API."""
    return {"api": "v1", "message": "pong"}
