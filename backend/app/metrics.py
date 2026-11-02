
"""MemoryMedic AI — Historical telemetry API.

Reads actual MemoryMedic demo CSV files and returns
validated numeric telemetry for dashboards and analysis.
"""

import csv
import math
from collections import deque
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query


router = APIRouter(
    prefix="/api/v1",
    tags=["Metrics"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"

Workload = Literal[
    "normal_workload",
    "burst_workload",
    "cache_growth",
    "linear_leak",
]

REQUIRED_FIELDS = {
    "timestamp_ms",
    "rss_kb",
    "threads",
}

INTEGER_FIELDS = {
    "timestamp_ms",
    "rss_kb",
    "virtual_memory_kb",
    "peak_rss_kb",
    "threads",
    "minor_page_faults",
    "major_page_faults",
}

FLOAT_FIELDS = {
    "rss_growth_kb_s",
    "minor_faults_s",
    "major_faults_s",
    "risk_score",
}


def convert_sample(row: dict, line_number: int) -> dict:
    """Convert known numeric fields while preserving labels."""

    result = {}

    for field, value in row.items():
        if field is None or value is None:
            raise ValueError(
                f"Malformed CSV row at line {line_number}"
            )

        if field in INTEGER_FIELDS | FLOAT_FIELDS:
            if not value.strip():
                if field in REQUIRED_FIELDS:
                    raise ValueError(
                        f"Missing {field} at line {line_number}"
                    )
                result[field] = None
                continue

            try:
                if field in INTEGER_FIELDS:
                    number = int(value)
                    if number < 0:
                        raise ValueError("Negative integer")
                else:
                    number = float(value)
                    if not math.isfinite(number):
                        raise ValueError("Non-finite number")

            except ValueError as error:
                raise ValueError(
                    f"Invalid {field} at line {line_number}"
                ) from error

            result[field] = number
        else:
            result[field] = value

    return result


@router.get("/metrics")
def get_metrics(
    workload: Workload = "normal_workload",
    limit: int = Query(default=50, ge=1, le=500),
):
    """Return validated telemetry from the latest matching demo."""

    candidates = [
        path
        for path in DATA_ROOT.glob(
            f"demo_*/{workload}.csv"
        )
        if path.is_file()
    ]

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=f"No demonstration CSV found for {workload}",
        )

    source = max(
        candidates,
        key=lambda path: path.stat().st_mtime,
    )

    try:
        with source.open(
            newline="",
            encoding="utf-8-sig",
        ) as stream:
            reader = csv.DictReader(stream)

            headers = reader.fieldnames

            if (
                not headers
                or len(headers) != len(set(headers))
                or any(not name for name in headers)
                or not REQUIRED_FIELDS.issubset(headers)
            ):
                raise ValueError(
                    "Missing or invalid telemetry CSV headers"
                )

            samples = deque(maxlen=limit)

            for line_number, row in enumerate(reader, start=2):
                samples.append(
                    convert_sample(row, line_number)
                )

            if not samples:
                raise ValueError("Telemetry CSV is empty")

    except (OSError, csv.Error, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to read or validate telemetry CSV",
        ) from error

    return {
        "project": "MemoryMedic AI",
        "workload": workload,
        "source": str(source.relative_to(PROJECT_ROOT)),
        "count": len(samples),
        "samples": list(samples),
    }
