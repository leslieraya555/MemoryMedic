#!/usr/bin/env bash
# File: scripts/run_demo.sh
# Project: MemoryMedic
# Author: Leslie Raya
#
# Run bounded Linux workloads and validate their captured CSVs.
# Stop the monitor before its workload to avoid shutdown-time samples.
# Usage: bash scripts/run_demo.sh [seconds=25] [interval_ms=500] [window=8]
# Requires the CMake build and Python 3's standard library.

set -Eeuo pipefail

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    printf '%s\n' 'Run this script with bash; do not source it.' >&2
    return 1
fi
if [[ "$(uname -s)" != Linux ]]; then
    printf '%s\n' 'Run this script inside Linux, such as your Ubuntu Multipass shell.' >&2
    exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'Python 3 is required to validate the captured CSVs.' >&2
    exit 1
fi
if (( $# > 3 )); then
    printf '%s\n' 'Usage: bash scripts/run_demo.sh [seconds] [interval_ms] [window]' >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
DATA_DIR="${PROJECT_ROOT}/data"
DURATION_SECONDS="${1:-25}"
INTERVAL_MS="${2:-500}"
WINDOW_SIZE="${3:-8}"
for setting in "${DURATION_SECONDS}" "${INTERVAL_MS}" "${WINDOW_SIZE}"; do
    if ! [[ "${setting}" =~ ^[1-9][0-9]*$ ]]; then
        printf '%s\n' 'Duration, interval, and window must be positive whole numbers.' >&2
        exit 1
    fi
done
if (( WINDOW_SIZE < 2 )); then
    printf '%s\n' 'The analysis window must contain at least two samples.' >&2
    exit 1
fi

MEMORYMEDIC="${BUILD_DIR}/memorymedic"
WORKLOAD_NAMES=(normal_workload burst_workload cache_growth linear_leak)
WORKLOAD_LABELS=(normal normal normal leak)
for program in memorymedic "${WORKLOAD_NAMES[@]}"; do
    if [[ ! -x "${BUILD_DIR}/${program}" ]]; then
        printf 'Missing executable: %s\nBuild the project first.\n' "${BUILD_DIR}/${program}" >&2
        exit 1
    fi
done

mkdir -p "${DATA_DIR}"
RUN_TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
OUTPUT_DIR="$(mktemp -d "${DATA_DIR}/demo_${RUN_TIMESTAMP}_XXXXXXXX")"
workload_pid=""
monitor_pid=""
sleeper_pid=""

stop_owned_process() {
    # Call only for a direct child started by this script; always reap it.
    local child_pid="$1" attempt exit_status=0 forced=0
    if kill -0 "${child_pid}" 2>/dev/null; then
        kill -TERM "${child_pid}" 2>/dev/null || true
        for (( attempt=0; attempt<30; attempt++ )); do
            if ! kill -0 "${child_pid}" 2>/dev/null; then
                break
            fi
            sleep 0.1
        done
        if kill -0 "${child_pid}" 2>/dev/null; then
            kill -KILL "${child_pid}" 2>/dev/null || true
            forced=1
        fi
    fi
    wait "${child_pid}" 2>/dev/null || exit_status=$?
    if (( forced )); then
        return 124
    fi
    return "${exit_status}"
}

cleanup_processes() {
    # Retain partial output after an error or interrupt for diagnosis.
    if [[ -n "${monitor_pid}" ]]; then
        stop_owned_process "${monitor_pid}" || true
    fi
    if [[ -n "${workload_pid}" ]]; then
        stop_owned_process "${workload_pid}" || true
    fi
    if [[ -n "${sleeper_pid}" ]]; then
        stop_owned_process "${sleeper_pid}" || true
    fi
    return 0
}
trap cleanup_processes EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

validate_capture() {
    python3 - "$1" "$2" "$3" "${DURATION_SECONDS}" "${INTERVAL_MS}" <<'PYTHON'
import csv
import math
import sys
from pathlib import Path

path, label, run_id = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
duration, interval = int(sys.argv[4]), int(sys.argv[5])
positive = {"timestamp_ms", "rss_kb", "virtual_memory_kb", "peak_rss_kb", "threads"}
rates = {"rss_growth_kb_s", "minor_faults_s", "major_faults_s"}
required = positive | rates | {"label", "run_id"}
try:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        if len(header) != len(set(header)) or any(not name for name in header):
            raise ValueError("blank or duplicate CSV headers")
        if not required.issubset(header):
            raise ValueError("missing required telemetry columns")
        rows = list(reader)
    minimum = max(1, int(duration * 1000 / interval * 0.8))
    if len(rows) < minimum:
        raise ValueError(f"truncated capture: {len(rows)} samples; expected at least {minimum}")
    previous = None
    for number, row in enumerate(rows, 2):
        if None in row or any(value is None or value == "" for value in row.values()):
            raise ValueError(f"incomplete CSV row at line {number}")
        if row["label"] != label or row["run_id"] != run_id:
            raise ValueError(f"incorrect label or run ID at line {number}")
        values = {name: float(row[name]) for name in positive | rates}
        if not all(math.isfinite(value) for value in values.values()):
            raise ValueError(f"non-finite telemetry at line {number}")
        if any(values[name] <= 0 for name in positive):
            raise ValueError(f"zero or negative memory/time/thread measurement at line {number}")
        if any(not values[name].is_integer() for name in ("timestamp_ms", "threads")):
            raise ValueError(f"fractional timestamp or thread count at line {number}")
        if any(values[name] < 0 for name in ("minor_faults_s", "major_faults_s")):
            raise ValueError(f"negative fault rate at line {number}")
        timestamp = values["timestamp_ms"]
        if previous is not None and timestamp <= previous:
            raise ValueError(f"non-increasing timestamp at line {number}")
        previous = timestamp
except (OSError, ValueError, csv.Error) as error:
    raise SystemExit(f"Invalid capture {path}: {error}. Original rows were retained.")
print(f"Validated {len(rows)} samples: {path}", flush=True)
PYTHON
}

run_workload() {
    local workload_name="$1" label="$2" elapsed monitor_status=0
    local csv_path="${OUTPUT_DIR}/${workload_name}.csv"
    local work_log="${OUTPUT_DIR}/${workload_name}.log"
    local monitor_log="${OUTPUT_DIR}/${workload_name}.monitor.log"
    local run_id="${workload_name}_${OUTPUT_DIR##*/}"

    printf '\nRunning %s for %s seconds...\n' "${workload_name}" "${DURATION_SECONDS}"
    "${BUILD_DIR}/${workload_name}" >"${work_log}" 2>&1 &
    workload_pid="$!"
    # Waiting on a background sleep lets signal traps interrupt the wait.
    sleep 1 &
    sleeper_pid="$!"
    wait "${sleeper_pid}"
    sleeper_pid=""
    if ! kill -0 "${workload_pid}" 2>/dev/null; then
        printf 'Workload exited early; inspect %s\n' "${work_log}" >&2
        return 1
    fi
    "${MEMORYMEDIC}" monitor --pid "${workload_pid}" \
        --interval-ms "${INTERVAL_MS}" --window "${WINDOW_SIZE}" \
        --out "${csv_path}" --label "${label}" --run-id "${run_id}" \
        --quiet >"${monitor_log}" 2>&1 &
    monitor_pid="$!"

    for (( elapsed=0; elapsed<DURATION_SECONDS; elapsed++ )); do
        sleep 1 &
        sleeper_pid="$!"
        wait "${sleeper_pid}"
        sleeper_pid=""
        if ! kill -0 "${workload_pid}" 2>/dev/null || ! kill -0 "${monitor_pid}" 2>/dev/null; then
            printf 'A process exited early; inspect logs in %s\n' "${OUTPUT_DIR}" >&2
            return 1
        fi
    done

    # Stop/reap the monitor while its workload is still alive.
    stop_owned_process "${monitor_pid}" || monitor_status=$?
    monitor_pid=""
    if (( monitor_status != 0 && monitor_status != 143 )); then
        printf 'Monitor stop failed (status %s); inspect %s\n' "${monitor_status}" "${monitor_log}" >&2
        return 1
    fi
    if ! kill -0 "${workload_pid}" 2>/dev/null; then
        printf 'Workload exited before monitoring finished; inspect %s\n' "${work_log}" >&2
        return 1
    fi
    stop_owned_process "${workload_pid}" || true
    workload_pid=""
    validate_capture "${csv_path}" "${label}" "${run_id}"
}

printf 'MemoryMedic controlled workload demo\nOutput directory: %s\n' "${OUTPUT_DIR}"
for index in "${!WORKLOAD_NAMES[@]}"; do
    run_workload "${WORKLOAD_NAMES[$index]}" "${WORKLOAD_LABELS[$index]}"
done
printf '%s\n' 'All four demonstration CSVs passed basic telemetry checks.' \
    'This demonstration is not a training collection or an independent accuracy benchmark.' \
    >"${OUTPUT_DIR}/COMPLETE.txt"
printf '\nDemo complete. Validated CSV files and logs are in:\n  %s\n' "${OUTPUT_DIR}"
