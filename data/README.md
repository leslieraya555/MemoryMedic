# MemoryMedic Dataset

<!-- File: data/README.md | Author: Leslie Raya -->

MemoryMedic records Linux process-memory telemetry in CSV files. Independent executions of controlled workloads supply labeled observations for feature engineering, model training, and evaluation.

Generate measurements with the monitor. Keep original run files and their metadata together.

## Workloads and labels

| Workload | Behavior | Label |
| --- | --- | --- |
| `normal_workload` | Holds approximately 64 MiB and repeatedly accesses it. | `normal` |
| `burst_workload` | Temporarily allocates approximately 256 MiB, releases it, and repeats. | `normal` |
| `cache_growth` | Adds sixteen approximately 8 MiB cache entries, then stops growing. | `normal` |
| `linear_leak` | Retains approximately 1 MiB every 500 ms without deleting the blocks. | `leak` |

Burst and bounded-cache growth are legitimate increases in memory usage. The positive workload models unbounded retention; it does not reproduce every source-level leak mechanism.

## Bundled example files

| File | Intended label | Purpose |
| --- | --- | --- |
| `normal_demo.csv` | `normal` | Small stable-memory example. |
| `burst_demo.csv` | `normal` | Small temporary-allocation example. |
| `linear_leak_demo.csv` | `leak` | Validated example of sustained memory growth. |
| `example_provenance.json` | Not applicable | Collection identity and checksum for the replacement leak example. |

The replacement `linear_leak_demo.csv` is a new Linux capture, copied without editing its measurements. Its collection record identifies the source commit, sampling settings, row count, and checksum. It is an illustrative example, separate from the September 2026 model benchmark.

The earlier leak example contained a final zero-memory observation that the strict feature validator rejects. Its original bytes remain recoverable from repository history. Replacing the example does not change the original benchmark collections, fitted models, or historical results.

The repository does not bundle a cache example. New demonstration runs generate one alongside the other three workloads.

## Demonstrations and training collections

The short demonstration command is:

```bash
bash scripts/run_demo.sh
```

It creates a unique `data/demo_<timestamp>_<identifier>/` directory with four CSV files, workload logs, monitor logs, and a `COMPLETE.txt` marker after all four captures pass basic validation. The script stops each monitor before terminating its workload. Invalid or interrupted captures remain available for inspection and do not receive a completion marker.

Demonstrations use different sampling settings from the training collector. They support functional checks and are not automatically included in training.

Training collections contain:

| Entry | Contents |
| --- | --- |
| `raw/` | One original CSV for each independent workload execution. |
| `logs/` | Workload and monitor logs. |
| `runs.csv` | Relative CSV paths, workload names, labels, run IDs, sample counts, and requested durations. |
| `COMPLETE.txt` | Written after all planned collector runs finish and pass collection checks. |

The collector creates uniquely named `data/collection_<timestamp>_<identifier>/` directories. Completed batches and fitted models are generated outputs excluded from Git. Preserve them locally when reproducing a recorded experiment.

## Collect enough data for a fresh training run

Run these commands inside Linux from the repository root after building the C++ targets. See the [root README](../README.md#build-and-test-on-linux) for setup.

The trainer requires **at least five completed, independent runs of each of the four workloads**. On a fresh checkout, use:

```bash
bash scripts/collect_dataset.sh 5 40
```

The arguments request five repetitions per workload and 40 seconds per run: 20 runs in total, taking approximately 14 minutes including startup and shutdown. The collector accepts 1–20 repetitions and durations of 40–300 seconds.

From a Mac with the existing Multipass setup:

```bash
multipass exec memorymedic -- bash -lc 'cd /home/ubuntu/MemoryMedic && bash scripts/collect_dataset.sh 5 40'
```

Smaller batches are valid when supplementing existing collections. Three repetitions produce only three runs per workload; that batch alone is insufficient for training on a fresh checkout. Running the collector without arguments also defaults to three repetitions.

Keep the terminal open until collection completes. Every invocation creates a new batch and preserves earlier collections.

## Validate completed collections

Activate the Python environment described in the root README, then run:

```bash
python ml/train_model.py --check-only
```

For the existing Multipass environment, the equivalent Mac command is:

```bash
multipass exec memorymedic -- bash -lc 'cd /home/ubuntu/MemoryMedic && /home/ubuntu/memorymedic-ml-venv/bin/python ml/train_model.py --check-only'
```

A successful check ends with:

```text
CHECK PASSED. No model trained; no output files written.
```

The trainer discovers `data/collection_*/raw/*.csv`, skips incomplete batches, checks manifests and measurements, and verifies partition eligibility. Top-level bundled examples and `data/demo_*` directories are separate from this training input.

## Validate the bundled examples

From the repository root with the Python environment activated:

```bash
python - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("ml").resolve()))
from train_model import read_csv_strict
from feature_engineering import add_features

examples = {
    "normal_demo.csv": "normal",
    "burst_demo.csv": "normal",
    "linear_leak_demo.csv": "leak",
}
for name, label in examples.items():
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
PY
```

This validates the CSVs without loading a model, training, or changing stored rows. A passing input check is not an accuracy measurement.

The GitHub Actions workflow also validates these examples and checks the replacement leak example against its recorded checksum, row count, and run identity.

## Verify a fresh copy

For an isolated checkout, build, tests, CSV checks, collection, training, and prediction, run this Linux helper after publishing the updates:

```bash
bash scripts/verify_fresh_copy.sh --full
```

It creates a new directory under your home directory, uses a separate Python environment, and preserves a verification log and new experiment artifacts. Allow approximately 18–22 minutes including setup and the 20-run collection. Omit `--full` for the shorter build/test/example/demo checks.

## Telemetry and features

Raw inputs include timestamps, RSS, virtual memory, peak RSS, thread count, page-fault rates, and the C++ analyzer's RSS regression slope. CSV metadata identifies each run and its known synthetic label.

Python adds within-run RSS changes, rolling means and standard deviations, a virtual-to-resident-memory ratio, and a major-fault fraction. Rolling calculations use the current and preceding observations and reset at run boundaries. Ten observations do not necessarily represent ten seconds.

Invalid raw measurements, missing fields, duplicate timestamps within a run, and non-finite values are rejected. Defined initial derived-feature values may be zero when no history or fault activity exists. Labels, run IDs, workload names, and heuristic risk outputs are excluded from model features.

## Historical benchmark

The September 2026 benchmark contained **1,243 telemetry rows from 32 independent runs**, with eight executions of each workload.

| Partition | Runs per workload | Total runs | Rows |
| --- | ---: | ---: | ---: |
| Training | 6 | 24 | 933 |
| Validation | 1 | 4 | 154 |
| Test | 1 | 4 | 156 |

Entire runs remain in one partition. This is a grouped train/validation/test split; grouped k-fold cross-validation has not been implemented. A fresh five-repetition collection has 20 runs and different counts from the historical benchmark.

See the [evaluation report](../docs/evaluation_report.md) for the recorded results, independent-execution counts, software checks, and limitations.

## Data quality and interpretation

- Preserve original measurements, manifests, logs, and completion markers.
- Keep every `run_id` entirely within one partition.
- Assign labels from known workload behavior; use `unknown` for an arbitrary application's unverified behavior.
- Keep test runs out of fitting, model selection, and threshold tuning.
- Do not count correlated rows as independent experiments.
- Keep new collections and evaluations separately identified from historical results.
- Preserve rejected files for diagnosis instead of removing rows to obtain a favorable result.

The data comes from controlled synthetic programs. It does not establish reliable memory-leak detection across unfamiliar applications. Longer sessions, additional leak implementations, diverse normal behaviors, and measurements on other systems remain future evaluation work.
