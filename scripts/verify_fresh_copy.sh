#!/usr/bin/env bash
# File: scripts/verify_fresh_copy.sh
# Project: MemoryMedic
# Author: Leslie Raya
#
# Clone the published repository into a new directory and verify its workflow.
# Usage: bash scripts/verify_fresh_copy.sh [--full]
# Quick: build, CTest, Python tests, bundled examples, and a short live demo.
# Full: also collect 20 independent runs, train, and predict four demo CSVs.
# Keep all outputs and logs; never change an existing checkout or benchmark.

set -Eeuo pipefail

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    printf '%s\n' 'Run this script with bash; do not source it.' >&2
    return 1
fi
if (( $# > 1 )); then
    printf '%s\n' 'Usage: bash scripts/verify_fresh_copy.sh [--full]' >&2
    exit 1
fi
case "${1:-}" in
    '') CHECK_MODE=quick ;;
    --full) CHECK_MODE=full ;;
    --help|-h)
        printf '%s\n' 'Usage: bash scripts/verify_fresh_copy.sh [--full]' \
            'Default: build, tests, example validation, and a short demonstration.' \
            '--full: also collect five runs per workload, train, and predict.' \
            'Run inside Ubuntu. First publish the finishing updates to main.'
        exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 1 ;;
esac
if [[ "$(uname -s)" != Linux ]]; then
    printf '%s\n' 'Run this check inside Linux, such as your Ubuntu Multipass shell.' >&2
    exit 1
fi
for program in git cmake ctest c++ python3; do
    if ! command -v "${program}" >/dev/null 2>&1; then
        printf 'Missing command: %s\nOn Ubuntu install: sudo apt-get install build-essential cmake git python3 python3-venv python3-pip\n' "${program}" >&2
        exit 1
    fi
done

CHECK_ROOT="$(mktemp -d "${HOME}/MemoryMedic-verification.XXXXXXXX")"
exec > >(tee "${CHECK_ROOT}/verification.log") 2>&1
trap 'printf "Verification stopped with an error. Preserve the files and log in %s\n" "${CHECK_ROOT}" >&2' ERR
printf 'Verification directory: %s\nMode: %s\n' "${CHECK_ROOT}" "${CHECK_MODE}"

git clone https://github.com/leslieraya555/MemoryMedic.git "${CHECK_ROOT}/MemoryMedic"
cd "${CHECK_ROOT}/MemoryMedic"
git rev-parse HEAD
python3 -m venv "${CHECK_ROOT}/venv"
source "${CHECK_ROOT}/venv/bin/activate"
python -m pip install --disable-pip-version-check -r ml/requirements.txt

# Avoid excessive thread counts on small verification VMs.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-2}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-2}"

cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
./build/memorymedic --help
bash -n scripts/collect_dataset.sh
bash -n scripts/run_demo.sh
test -s ml/tests/test_ml_pipeline.py
python - <<'PYTHON'
import unittest

suite = unittest.defaultTestLoader.discover("ml/tests", pattern="test_*.py")
if suite.countTestCases() == 0:
    raise SystemExit("No Python tests discovered; verification failed.")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
PYTHON

python - <<'PYTHON'
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, str(Path("ml").resolve()))
from feature_engineering import add_features
from train_model import read_csv_strict

for name, label in (("normal_demo.csv", "normal"), ("burst_demo.csv", "normal"), ("linear_leak_demo.csv", "leak")):
    path = Path("data") / name
    frame = read_csv_strict(path)
    if "run_id" not in frame:
        frame["run_id"] = path.stem
    if "label" not in frame or not frame["label"].eq(label).all():
        raise SystemExit(f"Unexpected label in {path}")
    validated = add_features(frame)
    if validated["run_id"].nunique() != 1:
        raise SystemExit(f"Expected one run in {path}")
    print(f"PASS: {path} ({len(validated)} rows)")
record = json.loads(Path("data/example_provenance.json").read_text())
digest = hashlib.sha256(Path("data/linear_leak_demo.csv").read_bytes()).hexdigest()
if digest != record["sha256"]:
    raise SystemExit("Replacement example checksum does not match its collection record.")
PYTHON

if [[ "${CHECK_MODE}" == full ]]; then
    bash scripts/run_demo.sh 25 500 8
else
    bash scripts/run_demo.sh 5 500 8
fi

python - <<'PYTHON'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("ml").resolve()))
from feature_engineering import add_features
from train_model import read_csv_strict

demos = list(Path("data").glob("demo_*"))
if len(demos) != 1 or not (demos[0] / "COMPLETE.txt").is_file():
    raise SystemExit("Expected exactly one completed demonstration in this fresh checkout.")
for name in ("normal_workload", "burst_workload", "cache_growth", "linear_leak"):
    frame = add_features(read_csv_strict(demos[0] / f"{name}.csv"))
    print(f"PASS: fresh {name} ({len(frame)} rows)")
PYTHON

if [[ "${CHECK_MODE}" == full ]]; then
    printf '\nCollecting 20 new runs. Allow about 14 minutes for collection.\n'
    bash scripts/collect_dataset.sh 5 40
    python ml/train_model.py --check-only
    python ml/train_model.py
    python - <<'PYTHON'
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys

models = [p for p in Path("artifacts/ml").glob("training_*") if (p / "COMPLETE.txt").is_file()]
if len(models) != 1:
    raise SystemExit("Expected one completed training output in this fresh checkout.")
model_dir = models[0]
demo = next(Path("data").glob("demo_*"))
output = Path("artifacts/fresh_verification")
output.mkdir(parents=True, exist_ok=False)
for name in ("normal_workload", "burst_workload", "cache_growth", "linear_leak"):
    subprocess.run([
        sys.executable, "ml/predict_csv.py", str(demo / f"{name}.csv"),
        "--model", str(model_dir / "memorymedic_model.joblib"),
        "--rows", "5", "--out", str(output / f"{name}_predictions.csv"),
    ], check=True)
report = json.loads((model_dir / "evaluation.json").read_text())
if report["independent_runs"] != 20:
    raise SystemExit("Expected 20 new independent workload runs.")
summary = {
    "purpose": "Fresh-copy functional workflow verification on synthetic workloads",
    "author": "Leslie Raya",
    "completed_utc": datetime.now(timezone.utc).isoformat(),
    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "training_directory": str(model_dir),
    "demo_directory": str(demo),
    "independent_runs": report["independent_runs"],
    "selected_model": report["selected_model"],
    "test_metrics": report["test_metrics"],
    "notice": "New experiment, separate from the historical September benchmark. Predictions are functional checks, not another independent accuracy estimate.",
}
(output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Saved workflow evidence: {output.resolve()}")
PYTHON
fi

printf '\n%s verification passed. Files and log retained in:\n  %s\n' "${CHECK_MODE}" "${CHECK_ROOT}"
