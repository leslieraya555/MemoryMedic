
"""Read historical MemoryMedic telemetry from validated demo CSV files."""

import csv
from collections import deque
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1", tags=["Metrics"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"

Workload = Literal[
    "normal_workload",
    "burst_workload",
    "cache_growth",
    "linear_leak",
]


@router.get("/metrics")
def get_metrics(
    workload: Workload = "normal_workload",
    limit: int = Query(default=50, ge=1, le=500),
):
    """Return actual recorded telemetry from the newest matching demo."""

    candidates = [
        path
        for path in DATA_ROOT.glob(f"demo_*/{workload}.csv")
        if path.is_file()
    ]

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=f"No demonstration CSV found for {workload}",
        )

    source = max(candidates, key=lambda path: path.stat().st_mtime)

    try:
        with source.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)

            if not reader.fieldnames:
                raise ValueError("CSV is missing its header")

            samples = list(deque(reader, maxlen=limit))

    except (OSError, csv.Error, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to read telemetry CSV",
        ) from error

    return {
        "project": "MemoryMedic AI",
        "workload": workload,
        "source": str(source.relative_to(PROJECT_ROOT)),
        "count": len(samples),
        "samples": samples,
    }
