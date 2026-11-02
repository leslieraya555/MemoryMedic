
"""Tests for MemoryMedic's machine-learning prediction API."""

from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from backend.app import predictions
from backend.app.main import app
from ml.feature_engineering import MODEL_FEATURES


client = TestClient(app)


class FakeModel:
    """Predictable test model; does not use the real ML artifact."""

    def predict_proba(self, features):
        count = len(features)

        return np.column_stack(
            (
                np.full(count, 0.2),
                np.full(count, 0.8),
            )
        )


def valid_sample(timestamp_ms=1000):
    return {
        "timestamp_ms": timestamp_ms,
        "rss_kb": 1024,
        "virtual_memory_kb": 4096,
        "peak_rss_kb": 2048,
        "threads": 2,
        "rss_growth_kb_s": 1.5,
        "minor_faults_s": 0.0,
        "major_faults_s": 0.0,
        "run_id": "test_run",
    }


def test_prediction_success(monkeypatch):
    """Check successful feature engineering and prediction."""

    def fake_loader():
        return (
            Path(
                "artifacts/ml/training_test/"
                "memorymedic_model.joblib"
            ),
            {
                "model": FakeModel(),
                "features": list(MODEL_FEATURES),
                "threshold": 0.5,
            },
        )

    monkeypatch.setattr(
        predictions,
        "load_trained_model",
        fake_loader,
    )

    response = client.post(
        "/api/v1/predict",
        json={
            "samples": [
                valid_sample(1000),
                valid_sample(2000),
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 2
    assert data["threshold"] == 0.5
    assert data["predictions"][0]["prediction"] == "leak"
    assert data["predictions"][0]["leak_probability"] == 0.8


def test_prediction_rejects_missing_features():
    """Reject records missing required measurements."""

    sample = valid_sample()
    del sample["threads"]

    response = client.post(
        "/api/v1/predict",
        json={"samples": [sample]},
    )

    assert response.status_code == 422


def test_prediction_rejects_duplicate_timestamp():
    """Reject repeated timestamps belonging to the same run."""

    response = client.post(
        "/api/v1/predict",
        json={
            "samples": [
                valid_sample(1000),
                valid_sample(1000),
            ]
        },
    )

    assert response.status_code == 422


def test_prediction_handles_missing_model(
    tmp_path, monkeypatch
):
    """Return 503 when no saved model is available."""

    monkeypatch.setattr(
        predictions,
        "MODEL_ROOT",
        tmp_path,
    )

    response = client.post(
        "/api/v1/predict",
        json={"samples": [valid_sample()]},
    )

    assert response.status_code == 503
