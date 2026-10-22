#!/usr/bin/env bash

# File: scripts/run_demo.sh
# Project: MemoryMedic
# Author: Leslie Raya
#
# Description:
# Runs each controlled MemoryMedic workload for a limited amount of time and
# records process-memory telemetry in CSV format. Normal, burst, and cache
# growth are labeled "normal"; continuous unreleased allocation is labeled
# "leak".
#
# Usage:
#   bash scripts/run_demo.sh
#   bash scripts/run_demo.sh 25 500 8
#
# Optional arguments:
#   1. Run duration in seconds (default: 25)
#   2. Sampling interval in milliseconds (default: 500)
#   3. Analysis window size (default: 8)
#
# Requirements:
#   Build the project first with:
#     cmake -S . -B build
#     cmake --build build -j

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
DATA_DIR="${PROJECT_ROOT}/data"

DURATION_SECONDS="${1:-25}"
INTERVAL_MS="${2:-500}"
WINDOW_SIZE="${3:-8}"

if ! [[ "${DURATION_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: duration must be a positive whole number." >&2
    exit 1
fi

if ! [[ "${INTERVAL_MS}" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: sampling interval must be a positive whole number." >&2
    exit 1
fi

if ! [[ "${WINDOW_SIZE}" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: analysis window must be a positive whole number." >&2
    exit 1
fi

MEMORYMEDIC="${BUILD_DIR}/memorymedic"

declare -a WORKLOAD_NAMES=(
    "normal_workload"
    "burst_workload"
    "cache_growth"
    "linear_leak"
)

declare -a WORKLOAD_LABELS=(
    "normal"
    "normal"
    "normal"
    "leak"
)

if [[ ! -x "${MEMORYMEDIC}" ]]; then
    echo "Error: ${MEMORYMEDIC} was not found or is not executable." >&2
    echo "Build the project first:" >&2
    echo "  cmake -S . -B build" >&2
    echo "  cmake --build build -j" >&2
    exit 1
fi

for workload_name in "${WORKLOAD_NAMES[@]}"; do
    workload_path="${BUILD_DIR}/${workload_name}"
    if [[ ! -x "${workload_path}" ]]; then
        echo "Error: ${workload_path} was not found or is not executable." >&2
        echo "Build the project before running the demo." >&2
        exit 1
    fi
done

RUN_TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
OUTPUT_DIR="${DATA_DIR}/demo_${RUN_TIMESTAMP}"
mkdir -p "${OUTPUT_DIR}"

workload_pid=""
monitor_pid=""

cleanup_processes() {
    if [[ -n "${monitor_pid}" ]] && kill -0 "${monitor_pid}" 2>/dev/null; then
        kill "${monitor_pid}" 2>/dev/null || true
        wait "${monitor_pid}" 2>/dev/null || true
    fi

    if [[ -n "${workload_pid}" ]] && kill -0 "${workload_pid}" 2>/dev/null; then
        kill "${workload_pid}" 2>/dev/null || true
        wait "${workload_pid}" 2>/dev/null || true
    fi
}

trap cleanup_processes EXIT INT TERM

run_workload() {
    local workload_name="$1"
    local label="$2"
    local workload_path="${BUILD_DIR}/${workload_name}"
    local csv_path="${OUTPUT_DIR}/${workload_name}.csv"
    local log_path="${OUTPUT_DIR}/${workload_name}.log"
    local run_id="${workload_name}_${RUN_TIMESTAMP}"

    echo
    echo "Running ${workload_name} for ${DURATION_SECONDS} seconds..."

    "${workload_path}" >"${log_path}" 2>&1 &
    workload_pid="$!"

    # Give the workload time to start before MemoryMedic reads its /proc files.
    sleep 1

    "${MEMORYMEDIC}" monitor \
        --pid "${workload_pid}" \
        --interval-ms "${INTERVAL_MS}" \
        --window "${WINDOW_SIZE}" \
        --out "${csv_path}" \
        --label "${label}" \
        --run-id "${run_id}" \
        --quiet &
    monitor_pid="$!"

    sleep "${DURATION_SECONDS}"

    kill "${workload_pid}" 2>/dev/null || true
    wait "${workload_pid}" 2>/dev/null || true
    workload_pid=""

    # MemoryMedic should stop when the monitored process exits. Stop it
    # explicitly if it is still running after a short grace period.
    sleep 1
    if kill -0 "${monitor_pid}" 2>/dev/null; then
        kill "${monitor_pid}" 2>/dev/null || true
    fi
    wait "${monitor_pid}" 2>/dev/null || true
    monitor_pid=""

    if [[ -s "${csv_path}" ]]; then
        echo "Saved telemetry: ${csv_path}"
    else
        echo "Warning: no telemetry was written for ${workload_name}." >&2
    fi
}

echo "MemoryMedic controlled workload demo"
echo "Output directory: ${OUTPUT_DIR}"

for index in "${!WORKLOAD_NAMES[@]}"; do
    run_workload "${WORKLOAD_NAMES[$index]}" "${WORKLOAD_LABELS[$index]}"
done

trap - EXIT INT TERM

echo
echo "Demo complete. CSV files and workload logs are in:"
echo "  ${OUTPUT_DIR}"
