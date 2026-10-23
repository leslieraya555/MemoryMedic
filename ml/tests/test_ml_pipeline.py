"""MemoryMedic Python regression tests.

File: ml/tests/test_ml_pipeline.py
Author: Leslie Raya

Run from the MemoryMedic repository root:
    python -m unittest discover -s ml/tests -p "test_*.py" -v

These tests use small synthetic fixtures and temporary files. They do not
read or modify collected datasets, benchmark reports, or saved project models.
They exercise the feature and training APIs from feature schema 2-strict-per-run.
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from threadpoolctl import threadpool_limits

# The scripts use imports relative to ml/; make them work with unittest discovery.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from feature_engineering import MODEL_FEATURES, add_features  # noqa: E402
from train_model import (  # noqa: E402
    WORKLOAD_LABELS,
    calculate_metrics,
    load_dataset,
    read_csv_strict,
    split_runs,
    train_and_evaluate,
)


def telemetry(rss=(100.0, 200.0, 300.0), run_id="run_a"):
    """Construct a valid telemetry fixture with an explicit experiment identity."""
    memory = np.asarray(rss, dtype=float)
    return pd.DataFrame({
        "timestamp_ms": 1000 + np.arange(len(memory)) * 1000,
        "rss_kb": memory,
        "virtual_memory_kb": memory * 2,
        "peak_rss_kb": np.maximum.accumulate(memory),
        "threads": np.ones(len(memory), dtype=int),
        "rss_growth_kb_s": np.r_[0.0, np.diff(memory)],
        "minor_faults_s": np.full(len(memory), 3.0),
        "major_faults_s": np.full(len(memory), 1.0),
        "run_id": run_id,
    })


def run_records(count=8):
    return pd.DataFrame([
        {"run_id": f"{workload}_{index:03d}", "workload": workload, "label": label}
        for workload, label in WORKLOAD_LABELS.items()
        for index in range(count)
    ])


class TestFeatureEngineering(unittest.TestCase):
    def test_known_feature_values_and_units(self):
        features = add_features(telemetry())
        np.testing.assert_allclose(features["rss_delta"], [0.0, 100.0, 100.0])
        np.testing.assert_allclose(features["rss_mean_10"], [100.0, 150.0, 200.0])
        np.testing.assert_allclose(features["rss_std_10"], [0.0, np.sqrt(5000), 100.0])
        np.testing.assert_allclose(features["vm_to_rss_ratio"], [2.0, 2.0, 2.0])
        np.testing.assert_allclose(features["fault_ratio"], [0.25, 0.25, 0.25])

    def test_input_is_preserved_on_success_and_rejection(self):
        source = telemetry()
        original = source.copy(deep=True)
        add_features(source)
        assert_frame_equal(source, original)

        source.loc[1, "rss_kb"] = 0
        invalid_original = source.copy(deep=True)
        with self.assertRaises(ValueError):
            add_features(source)
        assert_frame_equal(source, invalid_original)

    def test_future_observation_does_not_change_past_features(self):
        prefix = telemetry((100.0, 110.0, 120.0))
        extended = telemetry((100.0, 110.0, 120.0, 1_000_000.0))
        assert_frame_equal(
            add_features(prefix)[MODEL_FEATURES],
            add_features(extended).iloc[:3][MODEL_FEATURES],
        )

    def test_features_do_not_cross_run_boundaries(self):
        source = pd.concat([
            telemetry((100.0, 120.0), "a"),
            telemetry((1000.0, 1500.0), "b"),
        ], ignore_index=True).iloc[[3, 0, 2, 1]]
        features = add_features(source)
        self.assertEqual(features["run_id"].tolist(), ["a", "a", "b", "b"])
        np.testing.assert_allclose(features["rss_delta"], [0.0, 20.0, 0.0, 500.0])
        np.testing.assert_allclose(features["rss_mean_10"], [100.0, 110.0, 1000.0, 1250.0])

    def test_rolling_window_uses_last_ten_samples(self):
        features = add_features(telemetry((1000.0,) + (10.0,) * 10))
        self.assertAlmostEqual(features["rss_mean_10"].iloc[-1], 10.0)
        self.assertAlmostEqual(features["rss_std_10"].iloc[-1], 0.0)

    def test_zero_fault_count_has_finite_zero_ratio(self):
        source = telemetry()
        source[["minor_faults_s", "major_faults_s"]] = 0.0
        features = add_features(source)
        np.testing.assert_array_equal(features["fault_ratio"], 0.0)
        self.assertTrue(np.isfinite(features[MODEL_FEATURES].to_numpy()).all())

    def test_memory_decreases_are_valid(self):
        features = add_features(telemetry((300.0, 200.0, 100.0)))
        np.testing.assert_allclose(features["rss_delta"], [0.0, -100.0, -100.0])

    def test_label_and_heuristic_changes_do_not_change_model_inputs(self):
        first = telemetry()
        first["label"] = "normal"
        first["workload"] = "normal_workload"
        first["risk_score"] = 0.0
        first["risk_level"] = "low"
        second = first.copy()
        second["label"] = "leak"
        second["workload"] = "linear_leak"
        second["risk_score"] = 100.0
        second["risk_level"] = "high"
        excluded = {"label", "workload", "run_id", "risk_score", "risk_level", "target"}
        self.assertTrue(excluded.isdisjoint(MODEL_FEATURES))
        assert_frame_equal(add_features(first)[MODEL_FEATURES], add_features(second)[MODEL_FEATURES])

    def test_empty_missing_and_duplicate_columns_are_rejected(self):
        source = telemetry()
        invalid_frames = (
            source.iloc[:0],
            source.drop(columns=["rss_kb"]),
            pd.concat([source, source[["rss_kb"]]], axis=1),
        )
        for frame in invalid_frames:
            with self.subTest(columns=list(frame.columns), rows=len(frame)):
                with self.assertRaises(ValueError):
                    add_features(frame)

    def test_invalid_raw_measurements_are_rejected(self):
        cases = (
            ("rss_kb", 0), ("rss_kb", -1),
            ("rss_kb", np.nan), ("rss_kb", np.inf),
            ("rss_kb", "not-a-number"),
            ("virtual_memory_kb", 0), ("peak_rss_kb", 0),
            ("timestamp_ms", 0), ("timestamp_ms", 1000.5),
            ("threads", 0), ("threads", 1.5),
            ("minor_faults_s", -1), ("major_faults_s", -1),
            ("run_id", None), ("run_id", "   "),
        )
        for column, value in cases:
            with self.subTest(column=column, value=value):
                source = telemetry()
                source[column] = source[column].astype(object)
                source.loc[1, column] = value
                with self.assertRaises(ValueError):
                    add_features(source)

    def test_duplicate_time_in_same_run_is_rejected(self):
        source = telemetry()
        source.loc[1, "timestamp_ms"] = source.loc[0, "timestamp_ms"]
        with self.assertRaisesRegex(ValueError, "Duplicate timestamp"):
            add_features(source)


class TestRunSplits(unittest.TestCase):
    def test_partitions_keep_all_runs_once_and_cover_each_workload(self):
        records = run_records()
        original = records.copy(deep=True)
        splits = split_runs(records, seed=42)
        assert_frame_equal(records, original)
        self.assertEqual(set(splits["run_id"]), set(records["run_id"]))
        self.assertFalse(splits["run_id"].duplicated().any())
        groups = {
            partition: set(splits.loc[splits["partition"].eq(partition), "run_id"])
            for partition in ("train", "validation", "test")
        }
        self.assertTrue(groups["train"].isdisjoint(groups["validation"]))
        self.assertTrue(groups["train"].isdisjoint(groups["test"]))
        self.assertTrue(groups["validation"].isdisjoint(groups["test"]))
        for workload in WORKLOAD_LABELS:
            counts = splits.loc[splits["workload"].eq(workload), "partition"].value_counts()
            self.assertEqual(counts.to_dict(), {"train": 6, "validation": 1, "test": 1})

    def test_fixed_seed_produces_reproducible_split(self):
        first = split_runs(run_records(), seed=42).set_index("run_id")["partition"].sort_index()
        shuffled = run_records().sample(frac=1, random_state=7)
        second = split_runs(shuffled, seed=42).set_index("run_id")["partition"].sort_index()
        pd.testing.assert_series_equal(first, second)

    def test_too_few_runs_or_missing_workload_is_rejected(self):
        for records in (run_records(4), run_records().query("workload != 'linear_leak'")):
            with self.subTest(rows=len(records)):
                with self.assertRaises(ValueError):
                    split_runs(records, seed=42)

    def test_duplicate_run_identity_is_rejected(self):
        records = run_records()
        records.loc[1, "run_id"] = records.loc[0, "run_id"]
        with self.assertRaisesRegex(ValueError, "unique"):
            split_runs(records, seed=42)


class TestCsvAndDatasetValidation(unittest.TestCase):
    def test_strict_reader_accepts_quoted_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quoted.csv"
            path.write_text('first,second\n"a,b",1\n', encoding="utf-8")
            result = read_csv_strict(path)
            self.assertEqual(result.iloc[0]["first"], "a,b")

    def test_strict_reader_rejects_malformed_csv(self):
        cases = {
            "duplicate_header": "a,a\n1,2\n",
            "blank_header": "a,\n1,2\n",
            "extra_value": "a,b\n1,2,3\n",
            "missing_value": "a,b\n1\n",
            "header_only": "a,b\n",
            "empty": "",
        }
        with tempfile.TemporaryDirectory() as directory:
            for name, text in cases.items():
                with self.subTest(case=name):
                    path = Path(directory) / f"{name}.csv"
                    path.write_text(text, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        read_csv_strict(path)

    def test_collector_manifest_and_completion_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "collection_test"
            raw_dir = session / "raw"
            raw_dir.mkdir(parents=True)
            csv_path = raw_dir / "normal.csv"
            source = telemetry((100.0,) * 40, run_id="fixture_normal_001")
            source["label"] = "normal"
            source.to_csv(csv_path, index=False)
            manifest_path = session / "runs.csv"
            manifest = pd.DataFrame([{
                "file": "raw/normal.csv", "workload": "normal_workload",
                "label": "normal", "run_id": "fixture_normal_001",
                "samples": 40, "duration_seconds": 40,
            }])
            manifest.to_csv(manifest_path, index=False)
            pattern = str(raw_dir / "*.csv")
            with redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "No completed"):
                    load_dataset(pattern)

            (session / "COMPLETE.txt").write_text("Fixture complete.\n", encoding="utf-8")
            data, records = load_dataset(pattern)
            self.assertEqual(len(data), 40)
            self.assertEqual(len(records), 1)
            self.assertTrue(data["target"].eq(0).all())
            self.assertEqual(len(records.iloc[0]["sha256"]), 64)

            manifest.loc[0, "samples"] = 39
            manifest.to_csv(manifest_path, index=False)
            with self.assertRaisesRegex(ValueError, "sample count"):
                load_dataset(pattern)
            manifest.loc[0, "samples"] = 40
            manifest.to_csv(manifest_path, index=False)

            source.loc[0, "label"] = "leak"
            source.to_csv(csv_path, index=False)
            with self.assertRaisesRegex(ValueError, "disagree with manifest"):
                load_dataset(pattern)


class TestMetricsAndModelPersistence(unittest.TestCase):
    def test_confusion_counts_and_threshold_boundary(self):
        # At threshold 0.5 the predictions are 0, 1, 0, 1: TN, FP, FN, TP.
        metrics = calculate_metrics(pd.Series([0, 0, 1, 1]), np.array([0.1, 0.5, 0.4, 0.9]), 0.5)
        for name in ("true_negatives", "false_positives", "false_negatives", "true_positives"):
            self.assertEqual(metrics[name], 1)
        for name in ("accuracy", "precision", "recall", "f1", "false_positive_rate", "false_negative_rate"):
            self.assertAlmostEqual(metrics[name], 0.5)

    def test_normal_only_metrics_do_not_invent_auc(self):
        metrics = calculate_metrics(pd.Series([0, 0]), np.array([0.1, 0.2]), 0.5)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["false_positives"], 0)
        self.assertIsNone(metrics["roc_auc"])
        self.assertIsNone(metrics["average_precision"])
        self.assertIsNone(metrics["false_negative_rate"])

    def test_model_round_trip_and_test_data_do_not_change_fitted_model(self):
        records = run_records(5)
        splits = split_runs(records, seed=42)
        frames = []
        for row in records.itertuples(index=False):
            values = (100.0, 200.0, 300.0) if row.label == "leak" else (100.0, 100.0, 100.0)
            frame = add_features(telemetry(values, row.run_id))
            frame["workload"] = row.workload
            frame["target"] = int(row.label == "leak")
            frames.append(frame)
        data = pd.concat(frames, ignore_index=True)
        test_ids = set(splits.loc[splits["partition"].eq("test"), "run_id"])
        changed = data.copy(deep=True)
        test_mask = changed["run_id"].isin(test_ids)
        changed.loc[test_mask, "target"] = 1 - changed.loc[test_mask, "target"]
        changed.loc[test_mask, MODEL_FEATURES] *= 1000.0

        # Thread limits keep this tiny integration test fast on shared CI runners.
        with threadpool_limits(limits=1), redirect_stdout(io.StringIO()):
            artifact, report = train_and_evaluate(data, splits, 0.5)
            changed_artifact, changed_report = train_and_evaluate(changed, splits, 0.5)
            probe = data[MODEL_FEATURES]
            before = artifact["model"].predict_proba(probe)
            after = changed_artifact["model"].predict_proba(probe)
            self.assertEqual(report["selected_model"], changed_report["selected_model"])
            np.testing.assert_allclose(before, after, rtol=0, atol=0)
            self.assertEqual(report["saved_model_fit_partitions"], ["train", "validation"])
            self.assertTrue(np.isfinite(before).all())
            self.assertTrue(((before >= 0) & (before <= 1)).all())
            np.testing.assert_allclose(before.sum(axis=1), 1.0)

            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "fixture_model.joblib"
                joblib.dump(artifact, path)
                reloaded = joblib.load(path)
                self.assertEqual(reloaded["features"], list(MODEL_FEATURES))
                np.testing.assert_allclose(reloaded["model"].predict_proba(probe), before, rtol=0, atol=0)


if __name__ == "__main__":
    unittest.main()
