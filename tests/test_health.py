"""Tests for the health endpoint."""

from fastapi.testclient import TestClient

from app.main import app # type: ignore

client = TestClient(app)


def test_health_returns_healthy() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "environment" in body


def test_root_returns_message() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "CyberSentinel is alive"


def test_v1_ping() -> None:
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"api": "v1", "message": "pong"}
