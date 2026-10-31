
"""Tests for MemoryMedic AI numeric telemetry endpoints."""

from fastapi.testclient import TestClient

from backend.app import metrics as metrics_module
from backend.app.main import app


client = TestClient(app)


def make_csv(tmp_path, monkeypatch, content):
    """Create an isolated test CSV."""

    data_root = tmp_path / "data"
    demo = data_root / "demo_test"
    demo.mkdir(parents=True, exist_ok=True)

    csv_file = demo / "normal_workload.csv"
    csv_file.write_text(content, encoding="utf-8")

    monkeypatch.setattr(
        metrics_module, "PROJECT_ROOT", tmp_path
    )
    monkeypatch.setattr(
        metrics_module, "DATA_ROOT", data_root
    )

    return csv_file


def test_metrics_reads_real_csv(tmp_path, monkeypatch):
    make_csv(
        tmp_path,
        monkeypatch,
        "timestamp_ms,rss_kb,threads,rss_growth_kb_s\n"
        "1000,1024,2,1.5\n"
        "2000,2048,3,2.75\n",
    )

    response = client.get(
        "/api/v1/metrics?workload=normal_workload&limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 2
    assert data["samples"][0]["timestamp_ms"] == 1000
    assert data["samples"][0]["rss_kb"] == 1024
    assert data["samples"][1]["rss_kb"] == 2048
    assert data["samples"][1]["threads"] == 3
    assert data["samples"][1]["rss_growth_kb_s"] == 2.75
    assert data["source"] == (
        "data/demo_test/normal_workload.csv"
    )


def test_metrics_missing_data(tmp_path, monkeypatch):
    monkeypatch.setattr(
        metrics_module, "DATA_ROOT", tmp_path
    )

    response = client.get(
        "/api/v1/metrics?workload=linear_leak"
    )

    assert response.status_code == 404


def test_metrics_rejects_invalid_workload():
    response = client.get(
        "/api/v1/metrics?workload=invalid_workload"
    )

    assert response.status_code == 422


def test_metrics_rejects_invalid_limit():
    response = client.get(
        "/api/v1/metrics?limit=1000"
    )

    assert response.status_code == 422


def test_metrics_rejects_invalid_number(
    tmp_path, monkeypatch
):
    make_csv(
        tmp_path,
        monkeypatch,
        "timestamp_ms,rss_kb,threads\n"
        "1000,not_a_number,2\n",
    )

    response = client.get("/api/v1/metrics")

    assert response.status_code == 500


def test_metrics_rejects_missing_columns(
    tmp_path, monkeypatch
):
    make_csv(
        tmp_path,
        monkeypatch,
        "timestamp_ms,rss_kb\n"
        "1000,1024\n",
    )

    response = client.get("/api/v1/metrics")

    assert response.status_code == 500


def test_metrics_rejects_nan(tmp_path, monkeypatch):
    make_csv(
        tmp_path,
        monkeypatch,
        "timestamp_ms,rss_kb,threads,risk_score\n"
        "1000,1024,2,nan\n",
    )

    response = client.get("/api/v1/metrics")

    assert response.status_code == 500
