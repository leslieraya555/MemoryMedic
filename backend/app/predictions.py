
"""MemoryMedic AI — Machine-learning prediction API.

Uses the existing MemoryMedic feature-engineering pipeline
and an already-trained, locally trusted model artifact.
"""

from functools import lru_cache
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, StrictInt

from ml.feature_engineering import MODEL_FEATURES, add_features


router = APIRouter(
    prefix="/api/v1",
    tags=["Predictions"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_ROOT = PROJECT_ROOT / "artifacts" / "ml"


class TelemetrySample(BaseModel):
    """Raw measurements required by the trained ML pipeline."""

    model_config = ConfigDict(extra="ignore")

    timestamp_ms: StrictInt = Field(ge=0)
    rss_kb: StrictInt = Field(gt=0)
    virtual_memory_kb: StrictInt = Field(gt=0)
    peak_rss_kb: StrictInt = Field(gt=0)
    threads: StrictInt = Field(gt=0)

    rss_growth_kb_s: FiniteFloat
    minor_faults_s: FiniteFloat = Field(ge=0)
    major_faults_s: FiniteFloat = Field(ge=0)

    run_id: str = Field(min_length=1, max_length=128)


class PredictionRequest(BaseModel):
    """Measurements belonging to one or more process runs."""

    samples: list[TelemetrySample] = Field(
        min_length=1,
        max_length=500,
    )


@lru_cache(maxsize=4)
def _load_joblib(path: str):
    """Cache a trusted local trained model."""
    return joblib.load(path)


def load_trained_model():
    """Find and validate the latest timestamped ML artifact."""

    candidates = sorted(
        MODEL_ROOT.glob(
            "training_*/memorymedic_model.joblib"
        )
    )

    if not candidates:
        raise HTTPException(
            status_code=503,
            detail="No trained MemoryMedic model was found",
        )

    model_path = candidates[-1]

    try:
        artifact = _load_joblib(str(model_path))

        if not isinstance(artifact, dict):
            raise ValueError("Unexpected model artifact")

        model = artifact["model"]
        features = list(artifact["features"])
        threshold = float(artifact["threshold"])

        if features != list(MODEL_FEATURES):
            raise ValueError("Model feature schema mismatch")

        if not hasattr(model, "predict_proba"):
            raise ValueError("Model does not support probabilities")

        if not math.isfinite(threshold) or not (
            0 <= threshold <= 1
        ):
            raise ValueError("Invalid decision threshold")

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="Saved ML model could not be loaded or validated",
        ) from error

    return model_path, artifact


@router.post("/predict")
def predict_memory_leak(request: PredictionRequest):
    """Classify telemetry using the original trained ML pipeline."""

    # Validate and calculate features before model inference.
    try:
        frame = pd.DataFrame(
            [sample.model_dump() for sample in request.samples]
        )

        data = add_features(frame)

    except (ValueError, TypeError, KeyError) as error:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid telemetry: {error}",
        ) from error

    model_path, artifact = load_trained_model()

    model = artifact["model"]
    features = list(artifact["features"])
    threshold = float(artifact["threshold"])

    try:
        probabilities = np.asarray(
            model.predict_proba(data[features]),
            dtype=float,
        )

        if probabilities.shape != (len(data), 2):
            raise ValueError("Unexpected model output shape")

        leak_probabilities = probabilities[:, 1]

        if (
            not np.isfinite(leak_probabilities).all()
            or (leak_probabilities < 0).any()
            or (leak_probabilities > 1).any()
        ):
            raise ValueError("Invalid model probabilities")

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="Model inference failed",
        ) from error

    results = []

    # add_features sorts records by run ID and timestamp.
    for (_, row), probability in zip(
        data.iterrows(),
        leak_probabilities,
    ):
        score = float(probability)

        results.append(
            {
                "run_id": str(row["run_id"]),
                "timestamp_ms": int(row["timestamp_ms"]),
                "rss_kb": int(row["rss_kb"]),
                "leak_probability": round(score, 6),
                "prediction": (
                    "leak" if score >= threshold else "normal"
                ),
            }
        )

    return {
        "project": "MemoryMedic AI",
        "model_run": model_path.parent.name,
        "threshold": threshold,
        "count": len(results),
        "predictions": results,
    }
