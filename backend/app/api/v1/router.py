from fastapi import APIRouter

from app.api.v1 import flows, predict
from app.core.logging import get_logger

logger = get_logger(__name__)

api_router = APIRouter(tags=["v1"])
api_router.include_router(predict.router)
api_router.include_router(flows.router)


@api_router.get("/ping", summary="Ping the v1 API")
async def ping() -> dict:
    logger.debug("Ping endpoint called")
    return {"api": "v1", "message": "pong"}
