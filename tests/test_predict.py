"""Tests for /api/v1/predict and model loading."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services import predictor

FIXTURES = Path(__file__).parent.parent / "backend" / "tests" / "fixtures"

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _load_model_for_tests() -> None:
    """Load the model before tests run.

    TestClient(app) doesn't trigger FastAPI's lifespan handler, so we
    call load_model() explicitly. Session scope means it runs once.
    """
    settings = get_settings()
    predictor.load_model(settings.model_path)


def _load(name: str) -> dict:
    with (FIXTURES / name).open(encoding="utf-8") as f:
        return json.load(f)


def test_model_is_loaded() -> None:
    """The model must be loaded at import time."""
    assert predictor.is_loaded(), f"Model failed to load: {predictor.load_error()}"


def test_health_reports_model_loaded() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["model_loaded"] is True
    assert body["model_error"] is None


def test_predict_benign() -> None:
    response = client.post("/api/v1/predict", json=_load("sample_benign.json"))
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "BENIGN"
    assert 0.0 <= body["confidence"] <= 1.0
    assert "BENIGN" in body["probabilities"]


def test_predict_ddos() -> None:
    response = client.post("/api/v1/predict", json=_load("sample_ddos.json"))
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "DDoS"
    assert body["confidence"] > 0.9


def test_predict_missing_features_returns_422() -> None:
    response = client.post(
        "/api/v1/predict",
        json={"features": {"Destination Port": 80}},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Missing features" in detail


def test_predict_empty_features_returns_422() -> None:
    response = client.post("/api/v1/predict", json={"features": {}})
    assert response.status_code == 422
