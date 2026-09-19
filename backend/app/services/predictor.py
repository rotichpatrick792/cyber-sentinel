"""Load the trained ML model and expose a simple predict() function.

Design:
  - Model is loaded once via load_model() (called from the app's lifespan).
  - If the file is missing or fails to load, we store the error and let
    the API keep running. The /predict endpoint returns 503 in that case.
  - Thread-safe read of the module-level singleton (GIL protects the
    assignment; we don't need a lock because loading happens once at startup).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib

logger = logging.getLogger(__name__)

# Module-level state. Populated by load_model().
_model: Any | None = None
_feature_names: list[str] | None = None
_classes: list[str] | None = None
_load_error: str | None = None


def load_model(path: str | Path) -> None:
    """Load the model bundle from disk. Called once at startup."""
    global _model, _feature_names, _classes, _load_error

    resolved = Path(path).resolve()
    try:
        bundle = joblib.load(resolved)
        _model = bundle["model"]
        _feature_names = list(bundle["feature_names"])
        _classes = list(bundle["classes"])
        _load_error = None
        logger.info(
            "Model loaded from %s (%d features, %d classes)",
            resolved,
            len(_feature_names),
            len(_classes),
        )
    except Exception as exc:
        _model = None
        _feature_names = None
        _classes = None
        _load_error = f"{type(exc).__name__}: {exc}"
        logger.error("Failed to load model from %s: %s", resolved, _load_error)


def is_loaded() -> bool:
    """True if the model is ready to serve predictions."""
    return _model is not None


def load_error() -> str | None:
    """Return the load error message, if any."""
    return _load_error


def feature_names() -> list[str]:
    """Return the feature names the model expects. Empty if not loaded."""
    return list(_feature_names) if _feature_names else []


def predict(features: dict[str, float]) -> dict:
    """Run inference on a single feature vector.

    Args:
        features: dict mapping feature name -> value. Must contain every
                  feature the model expects. Extra keys are ignored.

    Returns:
        {
            "label": str,               # predicted class
            "confidence": float,        # probability of the predicted class
            "probabilities": {class: prob, ...}
        }

    Raises:
        RuntimeError: if the model isn't loaded.
        ValueError: if a required feature is missing.
    """
    if _model is None or _feature_names is None or _classes is None:
        raise RuntimeError("Model not loaded")

    missing = [name for name in _feature_names if name not in features]
    if missing:
        raise ValueError(f"Missing features: {missing}")

    # Build the input in the exact order the model was trained on.
    row = [[float(features[name]) for name in _feature_names]]

    # predict_proba returns shape (1, n_classes).
    proba = _model.predict_proba(row)[0]

    # Argmax -> class index -> class label.
    best_idx = int(proba.argmax())
    label = _classes[best_idx]
    confidence = float(proba[best_idx])

    probabilities = {
        cls: float(p) for cls, p in zip(_classes, proba)
    }

    return {
        "label": label,
        "confidence": confidence,
        "probabilities": probabilities,
    }
