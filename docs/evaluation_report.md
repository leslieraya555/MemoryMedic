# MemoryMedic Evaluation Report

<!-- File: docs/evaluation_report.md | Author: Leslie Raya | Updated: October 26, 2026 -->


**Author:** Leslie Raya

**Model benchmark:** September 2026

**Software verification:** October 23, 2026

**Reviewed implementation:** Commit `d71ad064aeb70a9d1d46caedef98b22561f82162`

## 1. Objective and Scope

MemoryMedic combines Linux process monitoring, CSV collection, feature engineering, supervised classification, saved-model prediction, and automated verification.

The evaluation addresses two questions:

1. How did the selected classifier perform on additional executions of the included synthetic workloads?
2. Do the implemented collection, validation, feature-engineering, model, and testing workflows operate as expected in the verified examples?

The September experiment supplies model-performance measurements. The October checks supply additional software-verification evidence. Passing software tests or completing a demonstration does not establish a new model-accuracy estimate.

## 2. Evidence and Experiment Identity

The recorded benchmark is supported by the saved `evaluation.json` and `splits.csv` outputs from these local artifact directories:

- `artifacts/ml/training_20260903_234911_3yu1blll/`
- `artifacts/ml/training_20260908_190049_rdl5ioya/`

Both reports contain the same 32 run identities, partition assignments, and benchmark results. They record repeated training on one benchmark rather than independent studies.

The September 8 saved model was also used for later prediction smoke checks.

The reports record:

| Setting | Recorded value |
| --- | --- |
| Feature schema | `2-strict-per-run` |
| Split seed | `42` |
| Classification threshold | `0.50` |
| Model-selection metric | Validation F1 |
| Final model fitting data | Training plus validation partitions |
| Final evaluation data | Held-out test partition |

Source hashes in the reports match the feature-engineering and training files at the reviewed commit.

Generated collections and model artifacts are excluded from Git. Exact historical reproduction therefore requires the preserved original collections, manifests, split record, source code, and compatible environment.

A new collection reproduces the procedure but creates a different dataset.

## 3. Workload Design and Labels

Four controlled workload programs provide labeled examples of different memory behaviors.

| Workload | Controlled behavior | Label | Independent executions |
| --- | --- | --- | ---: |
| `normal_workload` | Maintains approximately 64 MiB of allocated memory and repeatedly accesses it. | `normal` | 8 |
| `burst_workload` | Temporarily allocates approximately 256 MiB, releases it, and repeats. | `normal` | 8 |
| `cache_growth` | Adds sixteen approximately 8 MiB cache entries, then stops growing. | `normal` | 8 |
| `linear_leak` | Retains approximately 1 MiB every 500 ms without deleting the blocks. | `leak` | 8 |

Labels are assigned from the designed workload behavior and checked against the collector manifest.

Burst and cache workloads provide normal examples with legitimate memory increases. They help evaluate whether the classifier can distinguish these controlled patterns from sustained unreleased allocation.

The positive workload models unbounded retention. It does not reproduce every source-level memory-leak mechanism. The program retains pointers to allocated blocks, and process telemetry alone does not identify lost references or allocation sites.

## 4. Dataset and Collection Integrity

The historical benchmark contains:

| Quantity | Recorded value |
| --- | ---: |
| Total telemetry rows | 1,243 |
| Independent executions | 32 |
| Workload implementations | 4 |
| Runs per workload | 8 |
| Normal workload implementations | 3 |
| Leak workload implementations | 1 |

Collector batches preserve the original measurements and experiment metadata.

| Collection entry | Purpose |
| --- | --- |
| `raw/` | Separate original telemetry CSV files for independent executions. |
| `logs/` | Workload and monitor output for inspection. |
| `runs.csv` | File names, run IDs, workload names, labels, sample counts, and durations. |
| `COMPLETE.txt` | Completion marker written after the planned collection finishes successfully. |

Training accepts completed `collection_*/raw/*.csv` batches and checks each input against its manifest.

The current trainer requires at least five independent executions of every workload. A fresh five-repetition collection creates 20 executions. The larger historical benchmark resulted from accumulated completed batches.

The loader checks for:

- Malformed CSV rows.
- Duplicate or invalid column headers.
- Missing required columns.
- Inconsistent labels or run identities.
- Manifest and sample-count disagreements.
- Invalid durations or truncated runs.
- Invalid or non-finite numerical values.
- Duplicate timestamps within a run.

Incomplete batches are skipped. Invalid raw measurements are rejected instead of being silently replaced with artificial zeros.

## 5. Telemetry and Feature Engineering

The C++ collector reads:

- Resident memory from `VmRSS`.
- Virtual address-space size from `VmSize`.
- Peak resident memory from `VmHWM`.
- Thread count.
- Cumulative minor page-fault counts.
- Cumulative major page-fault counts.

It records timestamps, derives fault rates, and writes the analyzer's regression-based RSS slope.

Python generates the following twelve model inputs:

| Feature | Definition |
| --- | --- |
| `rss_kb` | Resident memory from `VmRSS`. |
| `virtual_memory_kb` | Virtual address-space size from `VmSize`. |
| `peak_rss_kb` | Resident-memory high-water mark from `VmHWM`. |
| `threads` | Current thread count. |
| `rss_growth_kb_s` | RSS regression slope over the recent C++ analysis window. |
| `minor_faults_s` | Minor-fault count change divided by elapsed seconds. |
| `major_faults_s` | Major-fault count change divided by elapsed seconds. |
| `rss_delta` | Difference from the preceding RSS observation in the same run. |
| `rss_mean_10` | Mean of the current and up to nine preceding RSS observations. |
| `rss_std_10` | Sample standard deviation over that rolling RSS window. |
| `vm_to_rss_ratio` | Virtual memory divided by RSS. |
| `fault_ratio` | Major-fault rate divided by total major-plus-minor fault rate. |

Feature calculations sort observations within each run and reset at run boundaries.

Rolling features use the current observation and available preceding observations. A ten-observation window is not necessarily ten seconds because its elapsed duration depends on the sampling interval.

Initial derived deltas and standard deviations are zero where history is insufficient. The fault ratio is zero when total fault activity is zero. These are defined derived-feature values; invalid raw measurements are rejected.

The following fields are excluded from the model feature list:

- Labels.
- Targets.
- Run IDs.
- Workload names.
- Heuristic risk scores and categories.

The feature-engineering implementation preserves the original input frame instead of modifying it in place.

## 6. Partitioning and Leakage Controls

Each workload contributed six training, one validation, and one test execution.

| Partition | Runs per workload | Total runs | Telemetry rows |
| --- | ---: | ---: | ---: |
| Training | 6 | 24 | 933 |
| Validation | 1 | 4 | 154 |
| Test | 1 | 4 | 156 |
| **Total** | **8** | **32** | **1,243** |

All observations from one `run_id` remain in a single partition. This prevents neighboring measurements from the same execution from appearing across training and evaluation partitions.

The fixed seed makes the assignment repeatable for the same run identities.

Additional leakage controls include:

1. Feature engineering uses causal calculations within each run.
2. Labels and experiment identifiers are excluded from model inputs.
3. Logistic regression's scaler is fitted as part of its training pipeline.
4. Both candidates are fitted on training data and compared on validation F1.
5. The selected configuration is fitted on the combined training and validation data.
6. Test data is excluded from fitting and candidate selection.

The saved final classifier therefore uses 28 training-plus-validation runs. Its final score is calculated on the four test runs.

This is a grouped train/validation/test evaluation. No grouped k-fold evaluation has been implemented or reported.

The test partition contains new executions of familiar programs rather than unfamiliar application implementations.

## 7. Candidate Models and Selection

Two candidate classifiers were compared using validation F1.

| Candidate | Validation F1 | Validation false positives | Validation false negatives |
| --- | ---: | ---: | ---: |
| Logistic regression | 0.904762 | 7 | 1 |
| Histogram-based gradient boosting | 1.000000 | 0 | 0 |

Logistic regression provides a standardized linear baseline with balanced class weights.

Histogram-based gradient boosting models nonlinear relationships and interactions among numerical features. The candidate configurations are fixed in the source, and the boosting classifier uses `early_stopping=False`.

Histogram-based gradient boosting achieved the higher validation F1 and was selected.

The fitted model saved to disk uses training plus validation data, with the held-out test runs excluded.

## 8. Aggregate Held-Out Results

The selected model was scored on 156 rows from four test runs at threshold 0.50.

| Metric | Recorded value |
| --- | ---: |
| Accuracy | 1.000 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| Average precision | 1.000 |
| ROC AUC | 1.000 |
| False-positive rate | 0.000 |
| False-negative rate | 0.000 |

### Confusion Matrix

| Actual / predicted | Normal | Leak |
| --- | ---: | ---: |
| Normal | 117 | 0 |
| Leak | 0 | 39 |

The positive class is `leak`.

| Classification outcome | Count |
| --- | ---: |
| True negatives | 117 |
| True positives | 39 |
| False positives | 0 |
| False negatives | 0 |

These results describe the included synthetic test executions. They do not establish perfect detection performance on unfamiliar applications.

## 9. Results by Workload and Metric Interpretation

Each test workload contributed 39 telemetry rows.

| Workload | Actual label | Correctly classified rows | False positives | False negatives |
| --- | --- | ---: | ---: | ---: |
| `normal_workload` | `normal` | 39 / 39 | 0 | 0 |
| `burst_workload` | `normal` | 39 / 39 | 0 | 0 |
| `cache_growth` | `normal` | 39 / 39 | 0 | 0 |
| `linear_leak` | `leak` | 39 / 39 | 0 | 0 |

Per-workload subsets contain only one class. ROC AUC is therefore undefined for those subsets and is stored as `null`.

Positive-class precision, recall, and F1 reported as zero by `zero_division=0` on an all-normal subset should be interpreted with its class support and confusion counts. This does not mean its 39 correctly classified normal rows were errors.

The aggregate metrics combine both classes.

These are row-level measurements over correlated telemetry rather than measurements over 156 independent experiments. There are only four independent held-out executions.

## 10. Recorded Environment

The saved reports record this historical training environment:

| Component | Version |
| --- | --- |
| Python | 3.14.4 |
| NumPy | 2.5.2 |
| pandas | 3.0.5 |
| scikit-learn | 1.9.0 |
| joblib | 1.6.0 |
| SciPy | 1.18.1 |
| threadpoolctl | 3.6.0 |

CI separately uses Python 3.12 and installs dependency versions satisfying `ml/requirements.txt`.

A passing CI run does not mean it recreated the exact historical training environment or reloaded every historical model artifact. Saved-model compatibility should be checked in the recorded environment.

## 11. October 23 Functional Verification

Later checks exercised the demonstration and saved-model workflow.

| Check | Observed result |
| --- | --- |
| Linux build and CTest | Build completed and the registered analyzer suite passed. |
| Fresh demonstration | Generated CSV telemetry for all four controlled workloads. |
| Saved-model prediction: normal workload | Recent displayed rows were classified as `normal`. |
| Saved-model prediction: burst workload | Recent displayed rows were classified as `normal`. |
| Saved-model prediction: cache growth | Recent displayed rows were classified as `normal`. |
| Saved-model prediction: linear leak | Recent displayed rows were classified as `leak`. |
| Local Python regression suite | All 21 tests passed. |

These prediction checks used the saved September model with fresh demonstration files.

They confirmed:

- Successful saved-model loading.
- Feature generation from new demonstration telemetry.
- Probability output.
- Expected classifications in the recent displayed rows.

These checks were not a prespecified independent benchmark. No new aggregate accuracy, detection latency, or calibration result is inferred from them.

An earlier example CSV was rejected for an invalid zero-memory measurement. This was appropriate validator behavior. A fresh collection supplied valid input for the later smoke check.

The precise cause of the older invalid measurement was not established by the rejection alone.

## 12. Python Regression Coverage

The committed suite contains 21 test methods.

| Category | Count | Behavior checked |
| --- | ---: | --- |
| Feature engineering | 11 | Known values, input preservation, causality, run boundaries, rolling length, valid decreases, invalid measurements, and excluded label/risk columns. |
| Grouped partitions | 4 | Disjoint complete runs, reproducibility, minimum counts, and duplicate identities. |
| CSV and dataset loading | 3 | Valid quoted CSV fields, malformed rows/headers, and manifest/completion consistency. |
| Metrics and model persistence | 3 | Confusion counts, threshold boundary, single-class metrics, probability validity, serialization, and test-data isolation. |
| **Total** | **21** | All passed in the verified local run. |

The integration test modifies only test features and labels, then verifies that model selection and the fitted model remain unchanged.

This supports the claim that the implemented selection and fitting procedure excludes test data. It does not by itself establish generalization or guard against all forms of future evaluation misuse.

The tests use temporary synthetic fixtures. They do not modify collected benchmark datasets or saved project models.

No numerical line-coverage percentage has been measured.

## 13. Continuous Integration Evidence

[GitHub Actions run 40029177958](https://github.com/leslieraya555/MemoryMedic/actions/runs/40029177958), titled **Add Python regression tests to CI**, succeeded for commit `d71ad06` on October 23, 2026.

| Job | Result | Scope |
| --- | --- | --- |
| C++ Build and Tests | Passed | CMake configuration/build, CTest, and executable help. |
| Python Validation | Passed | Regression suite, Python compilation, and module imports. |
| Shell Script Validation | Passed | Syntax of the collector and demonstration scripts. |

The shell job checks syntax without executing the workloads.

CI does not collect the historical dataset, retrain the historical model, or measure resource overhead. The successful workflow is software-verification evidence for that commit.

The existing historical screenshot documents earlier build and training output:

![Historical MemoryMedic build and training verification](images/memorymedic-build-test-training-results.png)

The linked October Actions run provides the newer automated-verification record.

## 14. Reproducibility Records

| Output | Audit purpose |
| --- | --- |
| Raw CSV files and `runs.csv` | Original observations and experiment identity. |
| Collection `COMPLETE.txt` | Successful completion of the planned collection. |
| `splits.csv` | Run assignments, input file identities, and SHA-256 checksums. |
| `evaluation.json` | Model selection, test results, environment, feature schema, and source checksums. |
| `requirements-used.txt` | Numerical package versions recorded by training. |
| `memorymedic_model.joblib` | Fitted selected classifier and prediction metadata. |
| Training `COMPLETE.txt` | Written after the training output steps complete. |

Keep these records together.

Repeated fitting of the same benchmark or rerunning smoke predictions should retain the original experiment identity.

New data, feature changes, threshold tuning, or candidate changes require separately identified evaluations.

## 15. Threats to Validity and Limitations

- All benchmark partitions contain executions of the same four synthetic programs.
- Only one positive workload implementation and a narrow set of allocation rates are represented.
- Absolute memory sizes and timing patterns may distinguish the programs without representing general leak behavior.
- Neighboring telemetry rows are correlated. Treating them as independent samples overstates the number of independent experimental units.
- Different sampling intervals change the elapsed horizon of sample-based features.
- The short demonstration uses different sampling and window settings from the training collector and supplies functional evidence.
- No independent evaluation on unrelated real applications has been reported.
- No grouped k-fold results, probability-calibration results, or confidence intervals have been reported.
- CPU overhead, monitor memory overhead, detection latency, and false alerts per hour remain unmeasured.
- Process-lifecycle races, PID reuse, non-atomic snapshot reads, and timestamp changes require further hardening and testing.
- Two saved training outputs on the same split are not two independent confirmations.

The perfect synthetic test score should therefore be interpreted within the scope of the available data and evaluation design.

## 16. Next Evaluation Plan

1. Add multiple leak implementations, slower allocation rates, and additional bounded-growth normal programs.
2. Collect longer independent runs with recorded operating conditions.
3. Define alert persistence, false-alert, and detection-latency measurements before testing them.
4. Evaluate unfamiliar applications after obtaining representative development data.
5. If cross-validation is needed, group development folds by run and preserve a separate final test set. Report variation and fold membership.
6. Measure baseline and monitored workload behavior using repeated comparable trials.
7. Assess calibration and thresholds on development data before a separate final operational-style evaluation.

The current evidence supports a working synthetic prototype and a tested software pipeline. Broader detection reliability and operational cost remain explicit questions for subsequent experiments.