#!/usr/bin/env bash
# MemoryMedic: collect labeled, independent synthetic workload runs.
# Save this file as scripts/collect_dataset.sh in your project.
# Run INSIDE Ubuntu: bash scripts/collect_dataset.sh 1 40
# Arguments: repetitions per workload, then seconds per run (40-300).
# Default: 3 repetitions x 4 workloads x 40 seconds = about 8 minutes.
# Requires Python 3 (standard library only); no pip packages are needed.
# Raw CSVs are preserved. This script does not merge data or train a model.

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    printf '%s\n' 'Run this script with bash; do not source it.' >&2
    return 1
fi
if [[ "$(uname -s)" != Linux ]]; then
    printf '%s\n' 'Open your Ubuntu Multipass shell first, then run this script.' >&2
    exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'Python 3 is required. Stop here and check your Ubuntu setup.' >&2
    exit 1
fi

exec python3 - "${BASH_SOURCE[0]}" "$@" <<'PYTHON'
import argparse
import csv
import math
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


WORKLOADS = (
    ("normal_workload", "normal"),
    ("linear_leak", "leak"),
    ("burst_workload", "normal"),
    ("cache_growth", "normal"),
)


class Interrupted(Exception):
    def __init__(self, signum):
        self.signum = signum


def interrupted(signum, _frame):
    raise Interrupted(signum)


def stop_child(process, stop_signal):
    """Stop only a process this collector started; always reap it."""
    if process is None:
        return False
    forced = False
    if process.poll() is None:
        process.send_signal(stop_signal)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            forced = True
    process.wait()
    return forced


def validate_csv(path, label, run_id, duration):
    """Reject suspect runs instead of silently deleting or relabeling rows."""
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {"timestamp_ms", "rss_kb", "virtual_memory_kb", "label", "run_id"}
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError(f"Unexpected CSV header in {path.name}; keep the file for inspection.")
        rows = list(reader)
    if len(rows) < int(duration * 0.8):
        raise RuntimeError(f"Too few samples ({len(rows)}) in {path.name}.")
    previous = None
    for number, row in enumerate(rows, start=2):
        if None in row or any(value is None or value == "" for value in row.values()):
            raise RuntimeError(f"Incomplete CSV row {number} in {path.name}.")
        if row["label"] != label or row["run_id"] != run_id:
            raise RuntimeError(f"Incorrect label/run ID at row {number} in {path.name}.")
        numeric_fields = ("timestamp_ms", "rss_kb", "virtual_memory_kb", "peak_rss_kb",
                          "threads", "minor_page_faults", "major_page_faults",
                          "rss_growth_kb_s", "minor_faults_s", "major_faults_s", "risk_score")
        for key in numeric_fields:
            if key in row and not math.isfinite(float(row[key])):
                raise RuntimeError(f"Non-finite {key} at row {number} in {path.name}.")
        if float(row["rss_kb"]) <= 0 or float(row["virtual_memory_kb"]) <= 0:
            raise RuntimeError(f"Zero/invalid memory sample at row {number} in {path.name}.")
        timestamp = int(row["timestamp_ms"])
        if previous is not None and timestamp <= previous:
            raise RuntimeError(f"Non-increasing timestamps in {path.name}.")
        previous = timestamp
    return len(rows)


def collect_run(build_dir, session, workload, label, repetition, duration):
    run_id = f"{session.name}_{workload}_{repetition:03d}"
    csv_path = session / "raw" / f"{run_id}.csv"
    work_log = session / "logs" / f"{run_id}.workload.log"
    monitor_log = session / "logs" / f"{run_id}.monitor.log"
    workload_process = monitor_process = None
    print(f"Running {workload}, repetition {repetition}, label={label}, {duration}s...", flush=True)
    with work_log.open("x") as work_stream, monitor_log.open("x") as monitor_stream:
        try:
            # Separate sessions let Ctrl+C interrupt the collector, which then
            # stops the monitor BEFORE the workload in a controlled order.
            workload_process = subprocess.Popen(
                [str(build_dir / workload)], stdout=work_stream,
                stderr=subprocess.STDOUT, start_new_session=True,
            )
            time.sleep(0.1)
            if workload_process.poll() is not None:
                raise RuntimeError(f"{workload} could not start; see {work_log}.")
            monitor_process = subprocess.Popen(
                [str(build_dir / "memorymedic"), "monitor",
                 "--pid", str(workload_process.pid), "--interval-ms", "1000",
                 "--window", "10", "--out", str(csv_path),
                 "--label", label, "--run-id", run_id, "--quiet"],
                stdout=monitor_stream, stderr=subprocess.STDOUT, start_new_session=True,
            )
            deadline = time.monotonic() + duration
            while time.monotonic() < deadline:
                if workload_process.poll() is not None:
                    raise RuntimeError(f"{workload} exited early; see {work_log}.")
                if monitor_process.poll() is not None:
                    raise RuntimeError(f"Monitor exited early; see {monitor_log}.")
                time.sleep(min(0.2, max(0, deadline - time.monotonic())))
            # SIGINT is equivalent to asking the monitor to stop with Ctrl+C.
            # Wait for its exit before terminating the workload, avoiding
            # artificial zero-RSS samples caused by workload shutdown.
            if stop_child(monitor_process, signal.SIGINT):
                raise RuntimeError(f"Monitor needed a forced stop; inspect {monitor_log}.")
            if monitor_process.returncode not in (0, -signal.SIGINT, 128 + signal.SIGINT):
                raise RuntimeError(f"Monitor failed with status {monitor_process.returncode}; see {monitor_log}.")
            if workload_process.poll() is not None:
                raise RuntimeError(f"{workload} exited unexpectedly; see {work_log}.")
        finally:
            # Finish cleanup even if a second interrupt arrives during shutdown.
            previous_handlers = {s: signal.signal(s, signal.SIG_IGN)
                                 for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
            try:
                try:
                    stop_child(monitor_process, signal.SIGTERM)
                finally:
                    stop_child(workload_process, signal.SIGTERM)
            finally:
                for signum, handler in previous_handlers.items():
                    signal.signal(signum, handler)
    samples = validate_csv(csv_path, label, run_id, duration)
    print(f"  Saved {samples} samples: {csv_path.name}", flush=True)
    return [f"raw/{csv_path.name}", workload, label, run_id, samples, duration]


def main():
    script_path = Path(sys.argv[1]).resolve()
    parser = argparse.ArgumentParser(
        prog="bash scripts/collect_dataset.sh",
        description="Collect four labeled synthetic workloads sequentially inside Ubuntu.",
    )
    parser.add_argument("repetitions", type=int, nargs="?", default=3)
    parser.add_argument("seconds", type=int, nargs="?", default=40)
    args = parser.parse_args(sys.argv[2:])
    if not 1 <= args.repetitions <= 20 or not 40 <= args.seconds <= 300:
        parser.error("Use 1-20 repetitions and 40-300 seconds per run.")
    root = script_path.parent.parent
    if script_path.parent.name != "scripts" or not (root / "CMakeLists.txt").is_file():
        raise RuntimeError("Save this file as scripts/collect_dataset.sh inside your MemoryMedic project.")
    build_dir = root / "build"
    for program in ("memorymedic", *(name for name, _ in WORKLOADS)):
        path = build_dir / program
        if not path.is_file() or not os.access(path, os.X_OK):
            raise RuntimeError(f"Missing or non-executable program: {path}. Build the project first.")
        # Popen will also report architecture errors clearly.
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    session = Path(tempfile.mkdtemp(prefix=f"collection_{stamp}_", dir=data_dir))
    (session / "raw").mkdir()
    (session / "logs").mkdir()
    print(f"Results: {session}\nPlanned: {4 * args.repetitions} runs, "
          f"about {4 * args.repetitions * args.seconds / 60:.1f} minutes.\n"
          "Keep this terminal open. Press Ctrl+C to stop safely.", flush=True)
    with (session / "runs.csv").open("x", newline="") as manifest:
        writer = csv.writer(manifest)
        writer.writerow(["file", "workload", "label", "run_id", "samples", "duration_seconds"])
        manifest.flush()
        for repetition in range(1, args.repetitions + 1):
            for workload, label in WORKLOADS:
                writer.writerow(collect_run(build_dir, session, workload, label,
                                             repetition, args.seconds))
                manifest.flush()
    (session / "COMPLETE.txt").write_text(
        "All planned runs passed basic CSV checks.\n"
        "Synthetic data only: this is not evidence of real-world model accuracy.\n"
        "Three normal workload types and one leak type are collected per repetition.\n"
        "Keep entire run IDs together when splitting training and evaluation data.\n",
        encoding="utf-8",
    )
    print(f"\nCollection complete. CSVs: {session / 'raw'}\n"
          f"Run summary: {session / 'runs.csv'}\n"
          "Review these results before training. Existing datasets were not modified.", flush=True)


for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    signal.signal(sig, interrupted)
try:
    main()
except Interrupted as exc:
    print("\nStopped. Test processes were cleaned up; partial files are retained for inspection.", file=sys.stderr)
    sys.exit(128 + exc.signum)
except (OSError, RuntimeError, ValueError, csv.Error) as exc:
    print(f"\nCollection stopped: {exc}\nPartial files are retained; do not train on this incomplete batch.",
          file=sys.stderr)
    sys.exit(1)
PYTHON
