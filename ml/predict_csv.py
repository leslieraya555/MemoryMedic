"""
File: predict_csv.py
Project: MemoryMedic
Author: Leslie Raya

Description:
    Loads a trained MemoryMedic machine-learning model and uses it to predict
    the probability of a memory leak for every row in a telemetry CSV file.

What must be added:
    1. train_model.py must be run successfully first.
    2. memorymedic_model.joblib must exist in the ml folder.
    3. A non-empty MemoryMedic telemetry CSV must be supplied.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from pandas.errors import EmptyDataError

from feature_engineering import add_features


def parse_arguments() -> argparse.Namespace:
    """Read prediction command-line options."""
    parser = argparse.ArgumentParser(
        description=(
            "Predict memory-leak probabilities from a MemoryMedic CSV."
        )
    )

    parser.add_argument(
        "csv",
        help="Telemetry CSV file to analyze.",
    )

    parser.add_argument(
        "--model",
        default="memorymedic_model.joblib",
        help="Trained MemoryMedic model file.",
    )

    parser.add_argument(
        "--out",
        default="",
        help="Optional filename for saving prediction results.",
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=20,
        help="Number of recent predictions to display.",
    )

    return parser.parse_args()


def main() -> None:
    """Load the model, generate predictions, and display the results."""
    arguments = parse_arguments()

    csv_path = Path(arguments.csv)
    model_path = Path(arguments.model)

    if not csv_path.exists():
        raise SystemExit(
            f"CSV file does not exist: {csv_path}"
        )

    if csv_path.stat().st_size == 0:
        raise SystemExit(
            f"The CSV file is empty: {csv_path}"
        )

    if not model_path.exists():
        raise SystemExit(
            f"Trained model does not exist: {model_path}\n"
            "Run train_model.py before making predictions."
        )

    try:
        data = pd.read_csv(csv_path)
    except EmptyDataError as error:
        raise SystemExit(
            f"The CSV file does not contain readable data: {csv_path}"
        ) from error

    if data.empty:
        raise SystemExit(
            f"The CSV file contains no measurements: {csv_path}"
        )

    if "run_id" not in data.columns:
        data["run_id"] = csv_path.stem

    try:
        data = add_features(data)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    artifact = joblib.load(model_path)

    required_artifact_keys = {
        "model",
        "features",
        "threshold",
    }

    missing_keys = (
        required_artifact_keys - set(artifact.keys())
    )

    if missing_keys:
        raise SystemExit(
            "The saved model file is missing required information: "
            + ", ".join(sorted(missing_keys))
        )

    model = artifact["model"]
    feature_names = artifact["features"]
    threshold = float(artifact["threshold"])

    probabilities = model.predict_proba(
        data[feature_names]
    )[:, 1]

    data["ml_leak_probability"] = probabilities

    data["ml_prediction"] = (
        data["ml_leak_probability"] >= threshold
    ).map(
        {
            True: "leak",
            False: "normal",
        }
    )

    display_columns = [
        "timestamp_ms",
        "rss_kb",
        "rss_growth_kb_s",
        "ml_leak_probability",
        "ml_prediction",
    ]

    number_of_rows = max(arguments.rows, 1)

    print("\nMemoryMedic prediction results")
    print("-----------------------------------------------")
    print(
        data[display_columns]
        .tail(number_of_rows)
        .to_string(index=False)
    )

    if arguments.out:
        output_path = Path(arguments.out)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data.to_csv(
            output_path,
            index=False,
        )

        print(f"\nPredictions saved to: {output_path}")


if __name__ == "__main__":
    main()