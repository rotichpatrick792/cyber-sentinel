"""Pydantic models used by the API layer.

Central location for request/response shapes. Keeps route files focused on
routing logic, not schema definitions.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """A single network flow, keyed by feature name."""

    features: dict[str, float] = Field(
        ...,
        description="Feature name -> value. Must contain every feature the model expects.",
    )


class PredictResponse(BaseModel):
    """Result of classifying one flow."""

    label: str
    confidence: float
    probabilities: dict[str, float]


class HealthResponse(BaseModel):
    """Shape of the /health response."""

    status: str
    environment: str
    model_loaded: bool
    model_error: str | None = None

class FlowRecord(BaseModel):
    """A classified flow as seen by the monitor."""

    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: int
    label: str
    confidence: float
    timestamp: str | None = None


class FlowsRecentResponse(BaseModel):
    flows: list[FlowRecord]
    total: int
