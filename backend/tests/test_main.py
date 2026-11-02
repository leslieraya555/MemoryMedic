
"""Tests for the MemoryMedic AI API."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["project"] == "MemoryMedic AI"
    assert data["status"] == "running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "memorymedic-api"
    assert "timestamp" in data
