# MemoryMedic Interview Guide

<!-- File: docs/interview_guide.md | Author: Leslie Raya | Updated: October 24, 2026 -->

**Author:** Leslie Raya

**Implementation reviewed:** Commit `d71ad06`, October 23, 2026.

This guide distinguishes implemented behavior, measured results, and proposed extensions. The September model benchmark and October software checks answer different questions and should be described separately.

## 1. A concise introduction

“MemoryMedic is a Linux process-memory monitoring system I built with C++ and Python. The C++ monitor reads `/proc` statistics, estimates memory growth, and writes telemetry to CSV. Python validates independent workload runs, creates causal features, and compares classification models. I evaluated it using normal, burst, cache-growth, and continuous-allocation workloads while keeping whole runs separate between training, validation, and testing. The current results demonstrate the synthetic pipeline; broader application testing remains future work.”

For a longer introduction, add:

“The important distinction is that increasing memory use can be legitimate. I included burst and bounded-cache workloads as normal examples. I also added strict data validation and regression tests because misleading input or a leaking evaluation split can make a model appear stronger than it is. The Python suite contains 21 tests, and GitHub Actions verifies the C++, Python, and shell portions.”

## 2. The problem and the limits of the claim

A high memory reading describes resource use. A leak diagnosis requires application context and evidence about allocations or retention over time. MemoryMedic estimates whether measured behavior resembles its labeled synthetic examples.

The `LinearLeak` program intentionally retains new allocations without deleting them. Its pointers remain stored in a vector. It is a controlled example of unbounded retention, rather than proof that the classifier can locate unreachable allocations or identify a source-code bug.

A developer would investigate a suspicious prediction using memory trends, allocation profilers, application logs, and knowledge of expected behavior. MemoryMedic does not identify the leaking allocation site or automatically repair it.

## 3. Responsibilities of the components

| Component | Implemented responsibility |
| --- | --- |
| `ProcessSample` | Holds one timestamped process snapshot and calculated rates. |
| `ProcReader` | Reads memory/thread fields from `/proc/<pid>/status` and fault counts from `/proc/<pid>/stat`. |
| `MemoryAnalyzer` | Fits an RSS trend over a recent window and measures consistency of sample-to-sample growth. |
| `RiskAssessment` | Stores the heuristic score, level, slope, stability, and explanation. |
| `TelemetryLogger` | Appends CSV measurements, risk output, labels, and run identity. |
| `MemoryMedic` | Coordinates sampling, rate calculations, bounded history, analysis, and logging. |
| `feature_engineering.py` | Validates raw measurements and creates causal numerical features per run. |
| `train_model.py` | Loads completed collections, creates grouped partitions, compares models, and saves evaluation artifacts. |
| `predict_csv.py` | Loads a saved model and classifies validated CSV rows. |

The live C++ heuristic and Python ML classifier are separate. Python inference currently runs over a CSV after collection; the C++ executable does not load a joblib model.

## 4. Operating-system measurements

| Measurement | Meaning in MemoryMedic |
| --- | --- |
| RSS | Pages currently resident in physical memory for the process, read from `VmRSS`. |
| Virtual memory | The process address-space size, read from `VmSize`; it is not a measurement of physical RAM consumption. |
| Peak RSS | The resident-memory high-water mark, read from `VmHWM`. |
| Threads | Thread count from the process status file. |
| Minor faults | Faults resolved without the major I/O needed for a major fault. |
| Major faults | Faults requiring I/O to bring in the required page. |

RSS is not the same as unique private memory; shared resident pages can contribute to multiple processes' RSS. Allocators can retain freed memory, so application-level deallocation does not always produce an immediate RSS decrease. These are reasons to avoid treating RSS alone as definitive leak evidence.

## 5. Why start with /proc?

“I started with `/proc` because it exposes useful per-process statistics through ordinary Linux files and supports a small, inspectable collector. That let me validate sampling, data quality, feature engineering, and evaluation before adding more complex telemetry.”

The collector polls snapshots rather than tracking every allocation. `/proc` field reads are not a single atomic snapshot, and short events between samples can be missed. Those limitations should inform the sampling interval and any future collector work.

eBPF is proposed future work. It could provide selected event-driven telemetry, but its permissions, compatibility, overhead, and actual detection benefit would need evaluation. An eBPF event stream does not automatically provide complete application-level allocation ownership or a leak diagnosis.

## 6. Growth estimation and the heuristic score

`MemoryAnalyzer` fits a line to RSS versus elapsed time over its configured recent sample window. With time in seconds and RSS in Linux kB units, the slope is in kB/s:

$$
m = \frac{n\sum_i t_i r_i - (\sum_i t_i)(\sum_i r_i)}{n\sum_i t_i^2 - (\sum_i t_i)^2}.
$$

Using several samples reduces dependence on a single change between adjacent readings. A larger window can smooth brief bursts but may delay recognition of a changing trend. A smaller window reacts faster and may be noisier.

The current implementation assigns an initial score using slope boundaries of 100, 500, and 2,000 kB/s, then multiplies the score by `0.75 + 0.25 * stability`. It assigns the final risk category from the adjusted score. These thresholds are heuristics, not parameters validated for every application.

Stability is derived from variation in adjacent growth rates. A stable allocation can have high stability and low growth, so stability alone does not imply a leak. The CSV's `rss_growth_kb_s` stores the regression-based slope produced by the analyzer.

## 7. Controlled workloads and ground truth

| Workload | Implemented behavior | Label |
| --- | --- | --- |
| Normal | Approximately 64 MiB allocated once and repeatedly accessed. | `normal` |
| Burst | Approximately 256 MiB temporarily allocated, then released, repeatedly. | `normal` |
| Cache growth | Sixteen approximately 8 MiB allocations, followed by a stable plateau. | `normal` |
| Linear leak | Approximately 1 MiB retained every 500 ms without release. | `leak` |

Labels come from the designed workload behavior and collector manifest. They are not generated from the heuristic score. A manually assigned `normal` or `leak` label on an unfamiliar program would not become trustworthy ground truth merely because the CLI accepted it.

“I included burst and cache growth because they challenge a simple ‘memory increasing means leak’ rule. However, four deterministic programs remain a narrow benchmark. The classifier could learn their specific sizes or rates rather than a general concept of leaking.”

## 8. Demonstration versus training collection

`run_demo.sh` creates short, timestamped demonstrations. The defaults are 25 seconds per workload, 500 ms sampling, and an eight-sample C++ window.

`collect_dataset.sh` creates independent training executions, a manifest, logs, and a completion marker. It uses a 1,000 ms interval and ten-sample analysis window, accepts 40–300 second runs, and stops the monitor before stopping the workload.

The trainer accepts completed collector batches, checks the manifest against each raw CSV, and requires at least five independent runs of every workload. It skips incomplete batches and rejects inconsistent or invalid data. Demonstration files are not automatically treated as training collections.

Different sampling settings change the elapsed duration represented by sample-based features. The short demonstration is a functional check; deployment at a new sampling rate requires its own evaluation.

## 9. The twelve model inputs

| Inputs | Meaning |
| --- | --- |
| `rss_kb`, `virtual_memory_kb`, `peak_rss_kb`, `threads` | Raw process measurements. |
| `rss_growth_kb_s` | C++ regression slope over recent RSS observations. |
| `minor_faults_s`, `major_faults_s` | Fault rates calculated from cumulative counts and elapsed time. |
| `rss_delta` | Difference from the preceding RSS sample within the same run. |
| `rss_mean_10`, `rss_std_10` | Rolling RSS mean and sample standard deviation over up to ten observations. |
| `vm_to_rss_ratio` | Virtual memory divided by resident memory. |
| `fault_ratio` | Major-fault rate divided by the sum of major and minor fault rates. |

When total fault activity is zero, `fault_ratio` is zero. The first RSS delta and an early standard deviation without enough history are initialized to zero. These are defined derived-feature values; invalid raw measurements are rejected instead of being silently filled with zeros.

## 10. Causality and leakage prevention

“Each feature uses only the current observation and available preceding observations in that run. Rolling statistics reset between run IDs. Appending a future observation must not change the earlier feature values.”

There are several distinct protections:

1. **Feature leakage:** Exclude labels, targets, workload names, run IDs, and heuristic risk scores from model inputs.
2. **Temporal leakage:** Use causal rolling windows and within-run deltas.
3. **Run leakage:** Assign every row of a run to one partition.
4. **Preprocessing leakage:** Fit logistic regression's scaler inside the training pipeline.
5. **Selection leakage:** Compare candidates using validation runs, then refit using training and validation only.
6. **Test reuse:** Preserve a final test set and avoid adapting the model to its results while still claiming an independent final evaluation.

Grouping by run addresses correlated executions. It does not establish generalization to unseen applications when every partition still uses the same four programs.

## 11. The recorded split

The September benchmark contained 32 executions and 1,243 telemetry rows:

| Partition | Runs | Rows |
| --- | ---: | ---: |
| Training | 24 | 933 |
| Validation | 4 | 154 |
| Test | 4 | 156 |

Each workload contributed six training, one validation, and one test run. The split seed was 42. The saved final classifier was fitted on the combined 28 training-plus-validation runs, then evaluated on the four test runs.

This is one grouped train/validation/test design. Grouped k-fold cross-validation is not implemented. Whether it is required for a particular submission must be checked against that submission's rubric.

## 12. Model choices

**Logistic regression** is a useful baseline for small tabular data. The current pipeline standardizes features, uses balanced class weights, and fits a linear decision boundary. A simpler baseline makes the benefit of a more flexible model easier to assess.

**Histogram-based gradient boosting** can capture nonlinear relationships and feature interactions without requiring a deep network. The implementation uses fixed candidate configurations and disables internal early stopping; the explicit validation partition controls model selection.

Candidates are selected by validation F1. In an exact tie, insertion order favors logistic regression. The selected candidate is cloned and fitted on training plus validation data before test evaluation.

“I did not add deep learning because the starting dataset is small, structured telemetry. I would first expand the data and assess strong baselines before justifying a more complex temporal model.”

## 13. The exact recorded results

| Candidate | Validation F1 |
| --- | ---: |
| Logistic regression | 0.904762 |
| Histogram-based gradient boosting | 1.000000 |

The selected gradient-boosting model produced 117 true negatives, 39 true positives, zero false positives, and zero false negatives on the 156 held-out rows. Aggregate accuracy, precision, recall, F1, average precision, and ROC AUC were each 1.000.

“The perfect score applies to four additional executions of the same synthetic programs. I would not describe it as 100% accurate real-world leak detection. The small number of independent runs and fixed workload implementations leave generalization largely untested.”

The stored September 3 and September 8 reports use the same input identities and split. They are records of repeated training on that benchmark, not two independent validation studies.

## 14. Explain the metrics

- **Precision:** Of rows predicted as leak, the fraction labeled leak. False alerts reduce precision.
- **Recall:** Of rows labeled leak, the fraction detected. Missed leaks reduce recall.
- **F1:** The harmonic mean of precision and recall at the selected threshold.
- **False-positive rate:** False positives divided by all actual normal rows.
- **ROC AUC:** Ranking performance across thresholds when both classes are present.
- **Average precision:** A summary of the precision-recall tradeoff based on scores.

The leak class is positive. At threshold 0.50, a score equal to the threshold is classified as leak. A per-workload test slice contains only one class, so ROC AUC is undefined there and the implementation records `null`. An F1 value of zero for an all-normal slice does not contradict correctly classifying every normal row; inspect confusion counts and false-positive rate as well.

Operational evaluation should also measure false alerts per monitoring hour and detection latency. Those measurements have not yet been reported.

## 15. Probability is not certainty

The prediction script outputs a model score between zero and one and a label using the stored threshold. These scores have not been calibrated on representative operational data.

“A score of 0.99 is strong output from this classifier, not a verified statement that an unfamiliar application has a 99% chance of leaking. I would validate calibration and alert thresholds on representative development data before interpreting the score operationally.”

Changing a threshold trades false positives against false negatives. Choose that threshold using development data and an explicit alerting objective, then evaluate the chosen procedure on an untouched test set.

## 16. Automated testing and CI

The current Python suite has 21 test methods:

| Area | Tests | Representative checks |
| --- | ---: | --- |
| Feature engineering | 11 | Known values, causal windows, run boundaries, invalid input, decreasing memory, and excluded labels/risk fields. |
| Grouped splits | 4 | Disjoint complete runs, fixed-seed reproducibility, minimum run counts, and duplicate IDs. |
| CSV and dataset validation | 3 | Quoted CSV fields, malformed rows/headers, and manifest/completion consistency. |
| Metrics and persistence | 3 | Threshold boundary/confusion counts, single-class metrics, model reload, and test-data isolation. |

The persistence/integration test changes only the test features and labels, reruns training, and verifies that the selected model and fitted predictions remain unchanged. It also verifies probability bounds and a joblib round trip using temporary fixtures.

CTest registers one `MemoryAnalyzerTests` suite containing eight scenarios. GitHub Actions has three jobs: C++ Build and Tests, Python Validation, and Shell Script Validation. Python CI uses version 3.12, executes the regression tests, and checks syntax and imports. Shell CI checks syntax without running the workloads.

The October 23 local test run passed, and [the CI run for `d71ad06`](https://github.com/leslieraya555/MemoryMedic/actions/runs/40029177958) succeeded. Twenty-one passing tests are not a test-coverage percentage or evidence of production detection accuracy.

## 17. Saved artifacts and reproducibility

A completed training output includes the joblib model, `evaluation.json`, `splits.csv`, `requirements-used.txt`, and `COMPLETE.txt`. These preserve model identity, feature schema, threshold, run assignments, input/source checksums, and environment versions.

“I can trace a recorded result back to its data identities and implementation. However, raw collections and models are generated local outputs rather than bundled with the repository. Another person can reproduce the procedure with fresh collection; exact historical reproduction needs the original inputs and a compatible recorded environment.”

Do not load untrusted joblib files. The prediction code relies on the stored feature list and a compatible preprocessing implementation; explicit schema-compatibility enforcement is a useful future hardening task.

## 18. Engineering difficulties and resolutions

- `/proc` required a Linux environment, so monitoring ran inside Ubuntu through Multipass.
- A Python environment inside a shared repository caused setup problems; keeping it outside the mount simplified operation.
- Too few independent executions prevented a defensible three-way split; more runs were collected.
- Raw invalid measurements required strict rejection and preserved files for diagnosis rather than silent repair.
- Mac and Ubuntu copies could differ; verifying actual paths prevented running old or missing files.
- A file existing in an editor did not guarantee it existed at the expected repository path. File checks, explicit staging, commits, and CI made the workflow observable.

Describe the problem, the evidence that exposed it, the change made, and how the change was checked. Avoid claiming that an assumed root cause has been proven without supporting logs or an experiment.

## 19. Process exit, errors, and timing

The monitor checks for a PID before starting and repeatedly during operation. If a read fails because the process disappeared, it stops the loop. Other read errors while the process still appears to exist are reported as failures.

Remaining edge cases include a process exiting between field reads, missing status fields returning zero, PID reuse, and wall-clock adjustments affecting timestamp-derived rates. The implementation uses a steady clock to schedule sampling, but records wall-clock timestamps for telemetry. Stronger process identity and separate monotonic timing for rates would improve robustness.

These are design considerations for future testing, not claims that the current test suite covers every process-lifecycle race.

## 20. Monitoring overhead and detection latency

Overhead and operational latency remain unmeasured. A sound plan would:

1. Select a repeatable bounded workload and fix the host, build, input, and duration.
2. Run repeated baseline trials without the monitor.
3. Run comparable trials with the monitor, varying trial order to reduce drift effects.
4. Record target throughput/runtime plus the monitor's CPU time and peak resident memory.
5. Repeat at several sampling intervals and report variation, not only the best run.

Compute runtime overhead as `(monitored_runtime - baseline_runtime) / baseline_runtime * 100%` when the workload has a meaningful finite runtime. For continuously running workloads, compare fixed-duration throughput and resource consumption instead.

Measure detection latency separately from sampling interval: define the known leak onset and alert rule, then measure time until that rule triggers. A 500 ms polling interval does not prove 500 ms leak detection.

## 21. Proposed banking integration

“A bank could evaluate MemoryMedic as an infrastructure diagnostic for approved Linux services, initially in staging. It would monitor process-resource telemetry from services such as transaction APIs or batch jobs, then send reviewed alerts to the existing observability system.”

Potential service and branch identifiers would be operational metadata. Customer records, account numbers, balances, and transaction contents are unnecessary for process-memory analysis.

The integration would need deployment permissions, process/container identity, representative baselines, access controls, retention rules, validated alert thresholds, and a documented response procedure. A prediction should prompt investigation. Automatic restarts would require separate engineering and operational approval because interrupting a service can affect in-flight work.

This integration is a proposal. The repository does not currently implement a central banking platform, transaction processing, a dashboard, or fleet orchestration.

## 22. Priorities for future work

| Priority | Experiment or improvement | Evidence it would add |
| --- | --- | --- |
| 1 | More normal applications, leak implementations, and allocation rates. | Tests whether success extends beyond four fixed programs. |
| 2 | Longer normal sessions and a defined alerting rule. | False alerts per hour and time to detection. |
| 3 | Controlled overhead measurements. | Resource cost and sampling tradeoffs. |
| 4 | Grouped cross-validation on development data, if needed. | Variation across development splits while preserving a final test set. |
| 5 | More process-reader, logger, CLI, and failure-path tests. | Coverage of collector and orchestration behavior. |
| 6 | Schema checks and deployment compatibility checks. | Safer handling of mismatched artifacts and environments. |
| Later | eBPF, container awareness, streaming inference, and fleet dashboards. | Benefits must be assessed against added complexity and operational cost. |

Automated CI already exists. The next testing task is expanding coverage and adding a bounded end-to-end smoke check, not starting CI from scratch.

## 23. A short demonstration narrative

1. Introduce the memory-growth problem and the distinction between a heuristic assessment and ML prediction.
2. Show the source organization and four workload definitions.
3. Show a bounded demonstration producing four telemetry files.
4. Load an existing trusted completed model and display recent predictions.
5. Show the saved evaluation and explain its grouped split and synthetic limitations.
6. Show the 21-test local result and successful three-job Actions run.
7. End with one measured result, one limitation, and the next experiment that would address it.

## 24. Preparation checklist

- [ ] Explain RSS, virtual memory, peak RSS, and page faults without reading notes.
- [ ] Explain the regression slope and sampling-window tradeoff.
- [ ] Distinguish the C++ heuristic score from the Python prediction.
- [ ] Explain the four workloads and the source of their labels.
- [ ] Name the protections against feature, temporal, run, and selection leakage.
- [ ] Explain why the current split is not k-fold cross-validation.
- [ ] Recall 32 runs, 1,243 rows, 24/4/4 runs, and the 117/39 confusion counts.
- [ ] Explain why a perfect synthetic score does not establish generalization.
- [ ] Explain what the 21 tests check and what they leave untested.
- [ ] Identify overhead and detection latency as future measurements.
- [ ] Demonstrate the saved-model workflow using paths that exist in the current environment.
- [ ] Describe proposed banking or eBPF integration as future work.

For full experimental details, use [the evaluation report](evaluation_report.md). For operational commands, use [the root README](../README.md).