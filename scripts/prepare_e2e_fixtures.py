"""Generate disposable integration-test CSVs and sklearn model.

The fixture lives under artifacts/e2e/ (gitignored), never under the real
training artifact or collected dataset locations. It is NOT benchmark data.
Run from the project root: python3 scripts/prepare_e2e_fixtures.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.feature_engineering import MODEL_FEATURES, add_features  # noqa: E402

FIXTURE_ROOT = ROOT / "artifacts" / "e2e"
CSV_ROOT = FIXTURE_ROOT / "data" / "demo_e2e"
MODEL_DIR = FIXTURE_ROOT / "models" / "training_e2e_fixture"

FIELDS = [
    "timestamp_ms", "rss_kb", "virtual_memory_kb", "peak_rss_kb", "threads",
    "rss_growth_kb_s", "minor_faults_s", "major_faults_s", "run_id", "label",
]


def create_samples(workload: str) -> list[dict]:
    rows = []
    previous = None
    peak = 0
    for i in range(40):
        if workload == "normal_workload":
            rss = 62_000 + (i % 4) * 15
        elif workload == "burst_workload":
            rss = 62_000 + (18_000 if i % 10 >= 7 else 0)
        elif workload == "cache_growth":
            rss = 62_000 + min(i, 25) * 140
        elif workload == "linear_leak":
            rss = 62_000 + i * 1_200
        else:
            raise ValueError(f"Unknown fixture workload: {workload}")
        peak = max(peak, rss)
        rows.append({
            "timestamp_ms": 1_730_000_000_000 + i * 1000,
            "rss_kb": rss,
            "virtual_memory_kb": rss + 6_000,
            "peak_rss_kb": peak,
            "threads": 1,
            "rss_growth_kb_s": 0.0 if previous is None else float(rss - previous),
            "minor_faults_s": 1.0 + (i % 3) * 0.25,
            "major_faults_s": 0.0,
            "run_id": f"e2e-{workload}",
            "label": "leak" if workload == "linear_leak" else "normal",
        })
        previous = rss
    return rows


def main() -> None:
    CSV_ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = []

    for workload in ("normal_workload", "burst_workload", "cache_growth", "linear_leak"):
        rows = create_samples(workload)
        with (CSV_ROOT / f"{workload}.csv").open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        all_rows.extend(rows)

    data = add_features(pd.DataFrame(all_rows))
    target = data["label"].eq("leak").astype(int)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=42))
    model.fit(data[MODEL_FEATURES], target)
    artifact = {
        "model": model,
        "features": list(MODEL_FEATURES),
        "threshold": 0.5,
        "fixture_only": True,
    }
    joblib.dump(artifact, MODEL_DIR / "memorymedic_model.joblib")

    (FIXTURE_ROOT / "NOTICE.json").write_text(json.dumps({
        "purpose": "Disposable E2E integration fixture only; not model-quality evidence",
        "workload_count": 4,
        "samples_per_workload": 40,
        "model": "LogisticRegression trained on the same synthetic fixture rows",
        "never_use_for": ["held-out accuracy", "production deployment", "benchmark comparisons"],
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Created E2E-only fixtures under {FIXTURE_ROOT}")
    print("40 samples per workload; separate saved test model; not a benchmark.")


if __name__ == "__main__":
    main()
