"""
File: feature_engineering.py
Project: MemoryMedic
Author: Leslie Raya

Build causal, per-run features from valid process telemetry. Invalid raw
measurements are rejected, not silently replaced with artificial zeros.
The model feature names remain compatible with the original prediction code.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_SCHEMA_VERSION = "2-strict-per-run"

MODEL_FEATURES = [
    "rss_kb", "virtual_memory_kb", "peak_rss_kb", "threads",
    "rss_growth_kb_s", "minor_faults_s", "major_faults_s", "rss_delta",
    "rss_mean_10", "rss_std_10", "vm_to_rss_ratio", "fault_ratio",
]

NUMERIC_INPUT_COLUMNS = [
    "timestamp_ms", "rss_kb", "virtual_memory_kb", "peak_rss_kb", "threads",
    "rss_growth_kb_s", "minor_faults_s", "major_faults_s",
]
REQUIRED_INPUT_COLUMNS = [*NUMERIC_INPUT_COLUMNS, "run_id"]


def validate_input_columns(frame: pd.DataFrame) -> None:
    """Check the schema without altering the input."""
    if frame.columns.duplicated().any():
        raise ValueError("Telemetry contains duplicate column names.")
    missing = [name for name in REQUIRED_INPUT_COLUMNS if name not in frame]
    if missing:
        raise ValueError("Missing telemetry columns: " + ", ".join(missing))
    if frame.empty:
        raise ValueError("Telemetry contains no measurements.")


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a validated copy sorted by run and time.

    Rolling windows contain the current and preceding observations only.
    They contain ten samples, not necessarily ten seconds. No label, run ID,
    workload name, or existing heuristic risk score becomes a model feature.
    """
    validate_input_columns(frame)
    data = frame.copy().reset_index(drop=True)

    def reject(mask: pd.Series, message: str) -> None:
        if mask.any():
            rows = (np.flatnonzero(mask.to_numpy())[:5] + 1).tolist()
            raise ValueError(f"{message}; data row(s) {rows}. No rows were changed.")

    reject(data["run_id"].isna(), "Missing run_id")
    data["run_id"] = data["run_id"].astype(str).str.strip()
    reject(data["run_id"].eq(""), "Blank run_id")

    for column in NUMERIC_INPUT_COLUMNS:
        numeric = pd.to_numeric(data[column], errors="coerce")
        reject(~np.isfinite(numeric), f"Invalid or non-finite {column}")
        data[column] = numeric

    for column in ("timestamp_ms", "rss_kb", "virtual_memory_kb", "peak_rss_kb", "threads"):
        reject(data[column].le(0), f"{column} must be greater than zero")
    for column in ("timestamp_ms", "threads"):
        reject(data[column].mod(1).ne(0), f"{column} must be a whole number")
    for column in ("minor_faults_s", "major_faults_s"):
        reject(data[column].lt(0), f"{column} cannot be negative")
    reject(data.duplicated(["run_id", "timestamp_ms"], keep=False),
           "Duplicate timestamp within a run")

    data = data.sort_values(["run_id", "timestamp_ms"], kind="stable").reset_index(drop=True)
    runs = data.groupby("run_id", sort=False)
    # Zero is intentional ONLY where a derived feature has no history yet.
    data["rss_delta"] = runs["rss_kb"].diff().fillna(0.0)
    data["rss_mean_10"] = runs["rss_kb"].transform(
        lambda values: values.rolling(10, min_periods=1).mean()
    )
    data["rss_std_10"] = runs["rss_kb"].transform(
        lambda values: values.rolling(10, min_periods=2).std()
    ).fillna(0.0)
    data["vm_to_rss_ratio"] = data["virtual_memory_kb"] / data["rss_kb"]
    total_faults = (data["minor_faults_s"] + data["major_faults_s"]).to_numpy(dtype=float)
    # This is a fraction from 0 to 1, not a percentage from 0 to 100.
    data["fault_ratio"] = np.divide(
        data["major_faults_s"].to_numpy(dtype=float), total_faults,
        out=np.zeros(len(data), dtype=float), where=total_faults > 0,
    )
    if not np.isfinite(data[MODEL_FEATURES].to_numpy(dtype=float)).all():
        raise ValueError("Derived features contain non-finite values; inspect the input.")
    return data
