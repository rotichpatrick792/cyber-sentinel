"""POST /api/v1/predict — run the ML model on a single flow."""

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import PredictRequest, PredictResponse
from app.services import predictor

router = APIRouter(tags=["predict"])


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
