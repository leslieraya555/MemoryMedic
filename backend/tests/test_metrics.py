
"""Tests for the MemoryMedic AI metrics API."""

from fastapi.testclient import TestClient

from backend.app import metrics as metrics_module
from backend.app.main import app


client = TestClient(app)


def test_metrics_reads_real_csv(tmp_path, monkeypatch):
    """Verify the API reads telemetry from a CSV file."""

    data_root = tmp_path / "data"
    demo = data_root / "demo_test"
    demo.mkdir(parents=True)

    csv_file = demo / "normal_workload.csv"

    csv_file.write_text(
        "timestamp_ms,rss_kb,threads\n"
        "1000,1024,2\n"
        "2000,2048,3\n",
        encoding="utf-8",
    )

    # Use isolated temporary paths for this test.
    monkeypatch.setattr(
        metrics_module,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        metrics_module,
        "DATA_ROOT",
        data_root,
    )

    response = client.get(
        "/api/v1/metrics",
        params={
            "workload": "normal_workload",
            "limit": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["project"] == "MemoryMedic AI"
    assert data["workload"] == "normal_workload"
    assert data["count"] == 2

    assert data["samples"][0]["rss_kb"] == "1024"
    assert data["samples"][1]["rss_kb"] == "2048"

    assert data["source"] == (
        "data/demo_test/normal_workload.csv"
    )


def test_metrics_missing_data(tmp_path, monkeypatch):
    """Verify the API returns 404 when data is missing."""

    monkeypatch.setattr(
        metrics_module,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        metrics_module,
        "DATA_ROOT",
        tmp_path / "data",
    )

    response = client.get(
        "/api/v1/metrics",
        params={
            "workload": "linear_leak",
        },
    )

    assert response.status_code == 404


def test_metrics_rejects_invalid_workload():
    """Verify unsupported workloads are rejected."""

    response = client.get(
        "/api/v1/metrics",
        params={
            "workload": "invalid_workload",
        },
    )

    assert response.status_code == 422


def test_metrics_rejects_invalid_limit():
    """Verify the API enforces its sample limit."""

    response = client.get(
        "/api/v1/metrics",
        params={
            "workload": "normal_workload",
            "limit": 1000,
        },
    )

    assert response.status_code == 422
