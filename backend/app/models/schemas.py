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
