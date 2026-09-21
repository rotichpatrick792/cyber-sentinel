"""Endpoints for the live flow feed.

POST /api/v1/flows       — record a classified flow (used by the monitor)
GET  /api/v1/flows/recent — return the most recent flows (used by the UI)
"""

from fastapi import APIRouter, Query

from app.models.schemas import FlowRecord, FlowsRecentResponse
from app.services import flow_store

router = APIRouter(tags=["flows"])


@router.post("/flows", response_model=FlowRecord, status_code=201)
async def record_flow(flow: FlowRecord) -> FlowRecord:
    """Store a classified flow. Called by network-monitor/detect.py."""
    record = flow_store.add_flow(flow.model_dump())
    return FlowRecord(**record)


@router.get("/flows/recent", response_model=FlowsRecentResponse)
async def get_recent_flows(
    limit: int = Query(50, ge=1, le=200),
) -> FlowsRecentResponse:
    """Return the most recent flows, newest first."""
    items = flow_store.recent(limit=limit)
    return FlowsRecentResponse(
        flows=[FlowRecord(**item) for item in items],
        total=flow_store.count(),
    )


@router.delete("/flows", status_code=204)
async def clear_flows() -> None:
    """Clear the flow buffer. Useful for demos and testing."""
    flow_store.clear()

