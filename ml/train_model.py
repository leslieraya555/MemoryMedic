"""
File: train_model.py
Project: MemoryMedic
Author: Leslie Raya

Train using completed collect_dataset.sh batches only. Split whole runs of
EACH workload into training, validation, and final test partitions. Select
the model on validation F1, refit it on training + validation, and evaluate
that exact model once on the untouched test runs. Never refit on test data.

At least five independent runs of each of the four workloads are required.
This is a small synthetic benchmark, not evidence of real-world accuracy.
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import platform
import tempfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from feature_engineering import FEATURE_SCHEMA_VERSION, MODEL_FEATURES, add_features

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKLOAD_LABELS = {
    "normal_workload": "normal", "linear_leak": "leak",
    "burst_workload": "normal", "cache_growth": "normal",
}
NOTICE = (
    "Preliminary synthetic benchmark: repeated runs of four fixed programs do not "
    "establish real-world leak detection. Metrics count correlated telemetry rows, "
    "not independent experiments. Do not tune the model after viewing test scores "
    "and then claim the same test runs are an independent final test."
)


def read_csv_strict(path: Path) -> pd.DataFrame:
    """Catch ragged rows and duplicate headers before pandas can reinterpret them."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        if not columns or len(set(columns)) != len(columns) or any(not c for c in columns):
            raise ValueError(f"Invalid or duplicate CSV header: {path}")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Ragged CSV row near line {reader.line_num}: {path}")
            rows.append(row)
    if not rows:
        raise ValueError(f"CSV contains no data: {path}")
    return pd.DataFrame(rows, columns=columns)


def load_dataset(pattern: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read raw telemetry only when its collector manifest and completion agree."""
    paths = sorted(Path(name).resolve() for name in glob.glob(pattern))
    if not paths:
        raise ValueError(f"No CSV files match: {pattern}")
    if len(paths) != len(set(paths)):
        raise ValueError("The CSV pattern includes the same file more than once.")
    manifests, frames, records, seen_ids, skipped = {}, [], [], set(), set()
    for path in paths:
        session = path.parent.parent
        if path.parent.name != "raw" or not session.name.startswith("collection_"):
            raise ValueError(f"Use completed collection_*/raw/*.csv files, not {path}")
        if not (session / "COMPLETE.txt").is_file():
            if session not in skipped:
                print(f"Skipping incomplete collection: {session.name}")
                skipped.add(session)
            continue
        if session not in manifests:
            manifest = read_csv_strict(session / "runs.csv")
            required = {"file", "workload", "label", "run_id", "samples", "duration_seconds"}
            if not required.issubset(manifest.columns):
                raise ValueError(f"Missing columns in {session / 'runs.csv'}")
            if manifest["file"].duplicated().any() or manifest["run_id"].duplicated().any():
                raise ValueError(f"Duplicate file or run ID in {session / 'runs.csv'}")
            manifests[session] = manifest
        manifest = manifests[session]
        matched = manifest[manifest["file"].eq(f"raw/{path.name}")]
        if len(matched) != 1:
            raise ValueError(f"CSV is not uniquely listed in its collector manifest: {path}")
        entry = matched.iloc[0]
        run_id, workload, label = entry["run_id"], entry["workload"], entry["label"]
        if not run_id.strip() or run_id != run_id.strip() or run_id in seen_ids:
            raise ValueError(f"Blank, padded, or reused run ID: {run_id!r}")
        if WORKLOAD_LABELS.get(workload) != label:
            raise ValueError(f"Unexpected workload/label in {session / 'runs.csv'}")
        raw = read_csv_strict(path)
        if "run_id" not in raw or "label" not in raw:
            raise ValueError(f"Missing run_id or label in {path}")
        if not raw["run_id"].eq(run_id).all() or not raw["label"].eq(label).all():
            raise ValueError(f"CSV labels or run IDs disagree with manifest: {path}")
        count, duration = int(entry["samples"]), int(entry["duration_seconds"])
        if not 40 <= duration <= 300 or count != len(raw) or count < int(duration * 0.8):
            raise ValueError(f"Invalid duration/sample count or truncated CSV: {path}")
        try:
            engineered = add_features(raw)
        except ValueError as error:
            raise ValueError(f"{path.name}: {error}") from error
        engineered["workload"] = workload
        engineered["target"] = int(label == "leak")
        frames.append(engineered)
        seen_ids.add(run_id)
        records.append({
            "run_id": run_id, "workload": workload, "label": label,
            "samples": count, "duration_seconds": duration, "source_csv": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    if not frames:
        raise ValueError("No completed, usable collector batches were found.")
    return pd.concat(frames, ignore_index=True), pd.DataFrame(records)


def split_runs(records: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Reserve about 20% validation and 20% test within EACH workload."""
    if records["run_id"].duplicated().any():
        raise ValueError("Run IDs must be unique.")
    rng = np.random.default_rng(seed)
    splits = records.copy()
    splits["partition"] = "train"
    for workload in WORKLOAD_LABELS:
        ids = sorted(records.loc[records["workload"].eq(workload), "run_id"])
        if len(ids) < 5:
            raise ValueError(
                f"{workload}: found {len(ids)} runs; need at least 5. "
                "Keep existing data and collect more independent repetitions."
            )
        shuffled = rng.permutation(ids)
        held_count = max(1, len(ids) // 5)
        splits.loc[splits["run_id"].isin(shuffled[:held_count]), "partition"] = "test"
        splits.loc[splits["run_id"].isin(shuffled[held_count:2 * held_count]), "partition"] = "validation"
    return splits


def calculate_metrics(labels: pd.Series, probabilities: np.ndarray, threshold: float) -> dict:
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    both = labels.nunique() == 2
    return {
        "rows": len(labels), "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "average_precision": float(average_precision_score(labels, probabilities)) if both else None,
        "roc_auc": float(roc_auc_score(labels, probabilities)) if both else None,
        "true_negatives": int(tn), "false_positives": int(fp),
        "false_negatives": int(fn), "true_positives": int(tp),
        "false_positive_rate": float(fp / (tn + fp)) if tn + fp else None,
        "false_negative_rate": float(fn / (tp + fn)) if tp + fn else None,
    }


def create_candidate_models() -> dict:
    return {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
        ]),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            learning_rate=0.06, max_iter=200, max_leaf_nodes=15,
            l2_regularization=1.0, early_stopping=False, random_state=42,
        ),
    }


def train_and_evaluate(data: pd.DataFrame, splits: pd.DataFrame, threshold: float) -> tuple[dict, dict]:
    """The test partition is not used to select or fit a model."""
    partition = data["run_id"].map(splits.set_index("run_id")["partition"])
    if partition.isna().any():
        raise ValueError("A telemetry run is absent from the split plan.")
    train = partition.eq("train")
    validation = partition.eq("validation")
    test = partition.eq("test")
    for name, mask in (("train", train), ("validation", validation), ("test", test)):
        if data.loc[mask, "target"].nunique() != 2:
            raise ValueError(f"{name} must contain both normal and leak examples.")
    features, target = data[MODEL_FEATURES], data["target"]
    candidates, validation_reports = create_candidate_models(), {}
    for name, model in candidates.items():
        model.fit(features.loc[train], target.loc[train])
        probs = model.predict_proba(features.loc[validation])[:, 1]
        validation_reports[name] = calculate_metrics(target.loc[validation], probs, threshold)
        print(f"Validation F1 / {name}: {validation_reports[name]['f1']:.3f}", flush=True)
    # Deterministic tie-break: prefer the simpler logistic regression model.
    winner = max(validation_reports, key=lambda name: validation_reports[name]["f1"])
    final_model = clone(candidates[winner])
    final_model.fit(features.loc[train | validation], target.loc[train | validation])
    test_probs = final_model.predict_proba(features.loc[test])[:, 1]
    test_rows = data.loc[test].reset_index(drop=True)
    test_report = calculate_metrics(test_rows["target"], test_probs, threshold)
    by_workload = {}
    for workload in WORKLOAD_LABELS:
        mask = test_rows["workload"].eq(workload)
        by_workload[workload] = calculate_metrics(test_rows.loc[mask, "target"], test_probs[mask], threshold)
    report = {
        "project": "MemoryMedic", "author": "Leslie Raya", "notice": NOTICE,
        "selected_model": winner, "selection_metric": "validation_f1", "threshold": threshold,
        "total_rows": len(data), "independent_runs": len(splits),
        "partitions": {name: {
            "run_ids": sorted(splits.loc[splits["partition"].eq(name), "run_id"].tolist()),
            "rows": int(partition.eq(name).sum()),
        } for name in ("train", "validation", "test")},
        "validation_metrics": validation_reports,
        "test_metrics": test_report, "test_metrics_by_workload": by_workload,
        "saved_model_fit_partitions": ["train", "validation"],
        "feature_schema": FEATURE_SCHEMA_VERSION,
    }
    artifact = {
        "project": "MemoryMedic", "author": "Leslie Raya", "model_name": winner,
        "model": final_model, "features": list(MODEL_FEATURES), "threshold": threshold,
        "feature_schema": FEATURE_SCHEMA_VERSION, "reports": report,
    }
    return artifact, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=str(PROJECT_ROOT / "data/collection_*/raw/*.csv"))
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--check-only", action="store_true", help="Validate data and splits without training.")
    parser.add_argument("--output-dir", type=Path, help="New directory only; existing outputs are never overwritten.")
    args = parser.parse_args()
    if not 0 < args.threshold < 1 or args.seed < 0:
        parser.error("Use a threshold between 0 and 1 and a nonnegative seed.")
    data, records = load_dataset(args.data)
    print(f"Validated {len(data)} rows from {len(records)} independent runs.", flush=True)
    print(records.groupby("workload").size().to_string(), flush=True)
    splits = split_runs(records, args.seed)
    print("\nRun split (each column keeps whole runs):")
    print(pd.crosstab(splits["workload"], splits["partition"]).to_string(), flush=True)
    if args.check_only:
        print("\nCHECK PASSED. No model trained; no output files written.")
        return
    if args.output_dir is None:
        parent = PROJECT_ROOT / "artifacts" / "ml"
        parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output = Path(tempfile.mkdtemp(prefix=f"training_{stamp}_", dir=parent))
    else:
        output = args.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=False)
    # Preserve the exact input identities and partition plan even if fitting fails.
    splits.to_csv(output / "splits.csv", index=False)
    artifact, report = train_and_evaluate(data, splits, args.threshold)
    report["seed"] = args.seed
    report["python_version"] = platform.python_version()
    packages = ("numpy", "pandas", "scikit-learn", "joblib", "scipy", "threadpoolctl")
    report["package_versions"] = {name: version(name) for name in packages}
    report["source_sha256"] = {name: hashlib.sha256(
        (Path(__file__).resolve().parent / name).read_bytes()).hexdigest()
        for name in ("train_model.py", "feature_engineering.py")}
    joblib.dump(artifact, output / "memorymedic_model.joblib")
    (output / "evaluation.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output / "requirements-used.txt").write_text(
        "".join(f"{name}=={value}\n" for name, value in report["package_versions"].items()), encoding="utf-8")
    (output / "COMPLETE.txt").write_text(NOTICE + "\n", encoding="utf-8")
    print(f"\nTraining complete. Selected: {report['selected_model']}")
    print(f"Final test F1: {report['test_metrics']['f1']:.3f}")
    print(f"Saved model and evaluation: {output}")
    print(NOTICE)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, csv.Error) as error:
        raise SystemExit(f"Stopped: {error}\nExisting datasets were not changed.") from error
