from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the app.

    Code before `yield` runs on startup.
    Code after `yield` runs on shutdown.
    """
    logger.info(
        "Starting %s v%s (env=%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    logger.info("CORS allowed origins: %s", settings.cors_origins)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def root() -> dict:
    logger.debug("Root endpoint hit")
    return {"message": "CyberSentinel is alive"}


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "healthy", "environment": settings.environment}


app.include_router(api_router, prefix=settings.api_v1_prefix)
