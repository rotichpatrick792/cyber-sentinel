"""POST /api/v1/predict — run the ML model on a single flow."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services import predictor

router = APIRouter(tags=["predict"])


class PredictRequest(BaseModel):
    """A single network flow, keyed by feature name.

    The set of expected features is defined by the trained model. Any
    feature the model was not trained on is ignored.
    """

    features: dict[str, float] = Field(
        ...,
        description="Feature name -> value. Must contain every feature the model expects.",
    )


class PredictResponse(BaseModel):
    label: str
    confidence: float
    probabilities: dict[str, float]


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Classify a single network flow",
)
async def predict(request: PredictRequest) -> PredictResponse:
    if not predictor.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model not loaded: {predictor.load_error() or 'unknown error'}",
        )

    try:
        result = predictor.predict(request.features)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return PredictResponse(**result)
