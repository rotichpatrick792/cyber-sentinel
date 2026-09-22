"""Endpoints for the live flow feed.

POST /api/v1/flows       — record a classified flow (used by the monitor)
GET  /api/v1/flows/recent — return the most recent flows (used by the UI)
DELETE /api/v1/flows     — clear the buffer

All endpoints require authentication (Bearer JWT) and are rate-limited.
"""

from fastapi import APIRouter, Depends, Query
from starlette.requests import Request

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.models.schemas import FlowRecord, FlowsRecentResponse
from app.models.user import User
from app.services import flow_store

router = APIRouter(tags=["flows"])


@router.post("/flows", response_model=FlowRecord, status_code=201)
@limiter.limit("200/minute")
async def record_flow(
    request: Request,
    flow: FlowRecord,
    current_user: User = Depends(get_current_user),
) -> FlowRecord:
    """Store a classified flow. Called by network-monitor/detect.py."""
    record = flow_store.add_flow(flow.model_dump())
    return FlowRecord(**record)


@router.get("/flows/recent", response_model=FlowsRecentResponse)
@limiter.limit("120/minute")
async def get_recent_flows(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
) -> FlowsRecentResponse:
    """Return the most recent flows, newest first."""
    items = flow_store.recent(limit=limit)
    return FlowsRecentResponse(
        flows=[FlowRecord(**item) for item in items],
        total=flow_store.count(),
    )


@router.delete("/flows", status_code=204)
@limiter.limit("10/minute")
async def clear_flows(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> None:
    """Clear the flow buffer. Useful for demos and testing."""
    flow_store.clear()
