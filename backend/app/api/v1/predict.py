"""POST /api/v1/predict — run the ML model on a single flow.

Requires authentication (Bearer JWT) and is rate-limited per client IP.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.models.schemas import PredictRequest, PredictResponse
from app.models.user import User
from app.services import predictor

router = APIRouter(tags=["predict"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Classify a single network flow",
)
@limiter.limit("600/minute")
async def predict(
    request: Request,
    payload: PredictRequest,
    current_user: User = Depends(get_current_user),
) -> PredictResponse:
    if not predictor.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model not loaded: {predictor.load_error() or 'unknown error'}",
        )

    try:
        result = predictor.predict(payload.features)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return PredictResponse(**result)
