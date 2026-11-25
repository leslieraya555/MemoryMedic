# MemoryMedic AI 2.0 — Independent Benchmark Plan

**Status:** Proposed experiment; **not yet conducted**.  
**Original historical baseline:** September 2026, four fixed synthetic workload programs.  
**Important:** These experiments are distinct from the five passing Playwright E2E tests. The Playwright suite checks software integration using fixture data and does **not** measure memory-leak detection accuracy.

## Research questions

1. How frequently does MemoryMedic issue leak predictions for previously unseen, correctly labeled normal Linux applications?
2. Can MemoryMedic detect new, controlled memory-growth patterns that were not used in model development?
3. What is the elapsed time between a known leak onset and first eligible positive prediction under a stated alerting rule?
4. How much extra CPU, RAM, and runtime overhead does the monitor impose?
5. How stable are the results across independent executions and workload conditions?

## Pre-experiment controls

- Run every collector and process-monitoring experiment **inside Linux** with access to `/proc`; keep your Mac copy for documentation, dashboard, and tests.
- Choose a **trusted, already trained model** before evaluating new workloads; record its SHA-256, threshold, feature schema, library versions, and original training-data identifiers. Do not include the new test runs in model fitting or threshold tuning.
- Use a release build. Record Linux distribution and kernel, machine/VM specifications, processor, CPU load, Python version, monitor sampling interval, monitoring window, workload duration, and any CPU/memory limits.
- Establish and document ground-truth labels, including the difference between *normal cache growth*, *temporary bursts*, and *unreleased allocations*. Do not infer a true leak just because RSS rises.
- Label independent executions with unique `run_id` values, keep the whole run together, and preserve a separate final test cohort. A row is **not** an independent experiment.
- Begin with a small feasibility pilot; predefine the main experiment and plan for at least 10 distinct runs per condition, more if resources allow. This is a suggested design target, not evidence that the benchmark has been performed.
- Avoid collecting sensitive production data or other users' processes. Use your own disposable test processes on a machine or VM you control.

## Experimental groups

| Group | Ground-truth condition | Example | What it probes |
| --- | --- | --- | --- |
| A | Normal | Idle Python HTTP server and routine file processing | False alarms on unfamiliar code |
| B | Normal | Bounded cache and transient memory bursts from new implementations | Normal growth confused for a leak |
| C | Deliberate leak | New bounded, controlled allocation-retention program | Detection of unseen leak implementation |
| D | Normal/negative control | Repeat representative jobs without monitoring | Baseline overhead |

For each monitored condition, collect raw `/proc` telemetry with the existing `build/memorymedic monitor` command and then run the frozen saved model with `ml/predict_csv.py`. Save the resulting per-row predictions without overwriting original collection runs.

## Primary metrics and definitions

- **Row-level false-positive rate:** `FP / (FP + TN)` for normal-labelled telemetry **rows**. Correlated rows make this descriptive, not an independent-run estimate.
- **Run-level false-alert rate:** fraction of truly normal runs with at least one qualifying alert. If alert suppression requires consecutive positive samples, pre-register the rule and report both raw and debounced rates.
- **Missed leak-run rate:** fraction of genuinely positive runs with no qualifying alert during the observation window.
- **Detection latency (seconds):** `time_of_first_qualifying_alert - known_ground_truth_leak_onset_time`. Requires an onset timestamp and a specified alerting/sampling policy. Since the current dashboard uses historical files, this is *retrospective/offline model timing*, not a measured live alert-delivery latency.
- **Monitoring CPU overhead:** change in workload CPU time/elapsed time **plus** the monitor process CPU cost; report the measuring method and baseline variation.
- **Monitoring memory overhead:** monitor RSS and changes to target-process peak RSS relative to comparable no-monitor runs.
- **Repeatability:** median, dispersion, and per-run data, including negative results.

## Reproducible verification of existing software (before the new experiments)

Run from the Linux repository root:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
bash scripts/run_demo.sh 25 500 8
```

The demo verifies the **existing synthetic workloads**, not generalization. It does **not** complete the independent benchmark above.

## Suggested artifact layout (all raw data may remain gitignored)

```text
artifacts/independent-benchmarks/<experiment-id>/
  protocol-version.txt
  environment.txt
  model-sha256.txt
  run-manifest.csv
  raw/
  predictions/
  process-logs/
  analysis/
    run-level-results.csv
    confusion-matrix.csv
    false-alert-summary.md
    overhead-summary.md
    detection-latency-summary.md
```

Create an accompanying repository document such as `docs/independent_benchmark_results.md` only after collecting data. Include paths, checksums, experiment commands, exact metric definitions, number of independent runs, uncertainty/variation, unflattering results, and limitations. Do not copy the original September 2026 classification scores into the new benchmark as if they were reproduced results.

## Proposed completion criteria

- The original model remains frozen while the new evaluation is performed.
- Ground truth is documented and sufficiently independent from the original fixed workload implementations.
- Repeatable per-run normal/leak results are available with raw evidence.
- False alarms, missed detections, and latency are reported with clear definitions.
- Resource overhead is compared with a reproducible unmonitored baseline.
- The evaluation report separates original synthetic results, browser software tests, and the new independent evaluation.
