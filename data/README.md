# MemoryMedic Dataset

**Project:** MemoryMedic
**Author:** Leslie Raya

## Purpose

The `data` directory stores process-memory telemetry collected by MemoryMedic. The CSV files contain measurements from controlled Linux workload executions and provide the input used to validate, train, and evaluate the memory-leak classification pipeline.

Measurements should be generated automatically by MemoryMedic. Manually entering, relabeling, or deleting individual telemetry rows could make the evaluation unreliable.

## Workloads and Labels

Four controlled workload programs represent different memory-use patterns:

| Workload          | Behavior                                                        | Machine-learning label |
| ----------------- | --------------------------------------------------------------- | ---------------------- |
| `normal_workload` | Allocates a stable amount of memory and repeatedly accesses it. | normal                 |
| `cache_growth`    | Simulates expected memory growth caused by caching.             | normal                 |
| `burst_workload`  | Produces temporary memory increases followed by recovery.       | normal                 |
| `linear_leak`     | Repeatedly allocates memory without releasing it.               | leak                   |

Cache growth and temporary bursts are labeled `normal` because increasing memory use is not automatically evidence of a leak. The classifier is expected to distinguish these patterns from sustained unreleased allocation.

## Directory Contents

The directory contains two types of data.

### Demonstration CSV Files

Small demonstration files are retained in Git so the telemetry format can be inspected without running a complete data collection.

* `normal_demo.csv`: Stable-memory example.
* `linear_leak_demo.csv`: Continuous-growth example.
* `burst_demo.csv`: Temporary memory-burst example.
* Cache-related example CSVs: Expected cache-growth behavior.

These files are useful for demonstrations and smoke tests. They are not treated as new independent evaluation data after they have already been used during development.

### Collected Dataset Batches

The collection script creates uniquely named directories using the following structure:

```text
data/collection_<date>_<time>_<identifier>/
├── raw/       # One telemetry CSV for each workload execution
└── runs.csv   # Run identifiers, workloads, labels, and collection metadata
```

Completed collection directories are generated data and are excluded from Git. The training program discovers completed batches locally and ignores incomplete collections.

## Telemetry Information

MemoryMedic records observations associated with a particular process and workload run. Depending on the collection stage, the stored information includes:

* A timestamp for each observation.
* A unique `run_id` identifying the workload execution.
* The workload name and expected label.
* Resident memory usage (`rss_kb`).
* Virtual memory usage.
* Peak resident memory.
* Thread count.
* Minor and major page-fault activity.
* Resident-memory growth rate.

The Python feature-engineering pipeline derives additional values, including memory changes, rolling averages, rolling variation, memory ratios, and fault ratios.

## Current Dataset Summary

The validated dataset contains **1,243 telemetry rows from 32 independent runs**.

| Workload          | Label  | Independent runs |
| ----------------- | ------ | ---------------: |
| `normal_workload` | normal |                8 |
| `cache_growth`    | normal |                8 |
| `burst_workload`  | normal |                8 |
| `linear_leak`     | leak   |                8 |
| **Total**         |        |           **32** |

The number of rows can vary slightly between future collections because process scheduling and sampling timing are not perfectly identical between runs.

## Data Partitioning

Telemetry rows from the same workload execution are correlated. The training pipeline therefore groups data by `run_id` before creating partitions. Every row from one run remains entirely in the training, validation, or test partition.

For each workload, the eight independent runs are divided into:

* 6 training runs
* 1 validation run
* 1 held-out test run

Across the four workloads, the split contains 24 training runs, 4 validation runs, and 4 test runs. The current method is a grouped train/validation/test split, not k-fold cross-validation.

## Collecting Additional Data

From the Linux repository root, run:

```bash
bash scripts/collect_dataset.sh 3 40
```

The first argument requests three repetitions of each workload. The second argument runs each workload for 40 seconds.

From the macOS terminal, data collection can be started inside Multipass with:

```bash
multipass exec memorymedic -- bash -lc 'cd /home/ubuntu/MemoryMedic && bash scripts/collect_dataset.sh 3 40'
```

Keep the terminal open until the script reports that collection is complete. Each execution creates a new directory and does not overwrite previous completed batches.

## Validating the Dataset

Run validation-only mode before training:

```bash
/home/ubuntu/memorymedic-ml-venv/bin/python ml/train_model.py --check-only
```

From the macOS terminal, run:

```bash
multipass exec memorymedic -- bash -lc 'cd /home/ubuntu/MemoryMedic && /home/ubuntu/memorymedic-ml-venv/bin/python ml/train_model.py --check-only'
```

The validation process checks completed collections, required fields, labels, run identifiers, timestamps, numerical values, and partition eligibility.

Successful validation ends with:

```text
CHECK PASSED. No model trained; no output files written.
```

## Data Quality Rules

* Do not manually change workload labels to improve model results.
* Do not place rows from one `run_id` in multiple partitions.
* Do not treat individual rows from the same run as independent experiments.
* Do not train on the held-out test runs.
* Do not tune the model after reviewing the final test score and then report the same test data as a new evaluation.
* Keep incomplete collection batches separate from validated training data.
* Preserve original CSV files when documenting or reproducing an experiment.

## Limitations

The dataset comes from four controlled synthetic programs executed in one Linux environment. It does not represent the full variety of memory behavior found in production applications.

Only one current workload represents the leak class. Therefore, high performance on these files does not prove that MemoryMedic can reliably detect every real-world memory leak.

Future data collection should include:

* More independent applications.
* Multiple types of memory leaks.
* Longer monitoring sessions.
* Different allocation rates.
* Production-like normal workloads.
* Additional Linux environments.
