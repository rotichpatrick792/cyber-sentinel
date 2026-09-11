from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="CyberSentinel API", version="0.1.0")


@app.get("/", tags=["root"])
async def root() -> dict:
    return {"message": "CyberSentinel is alive"}


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "healthy"}


app.include_router(api_router)