from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings # type: ignore

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)


@app.get("/", tags=["root"])
async def root() -> dict:
    return {"message": "CyberSentinel is alive"}


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "healthy", "environment": settings.environment}


app.include_router(api_router, prefix=settings.api_v1_prefix)
