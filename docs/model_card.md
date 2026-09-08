# MemoryMedic Model Card

## Model Details

- **Project:** MemoryMedic
- **Author:** Leslie Raya
- **Model:** Histogram-based gradient boosting classifier (`hist_gradient_boosting`)
- **Version:** September 2026
- **Status:** Preliminary synthetic prototype
- **Purpose:** Estimate whether Linux process telemetry resembles a memory leak.

## Model Summary

MemoryMedic monitors a Linux process, records memory-related telemetry, engineers numerical features, and uses a supervised classification model to estimate the probability of a memory leak. The selected model is a histogram-based gradient boosting classifier because it achieved the strongest validation F1 score among the evaluated candidates.

This model was trained on controlled synthetic workloads. Its results demonstrate that the implemented pipeline can distinguish the included workload patterns, but they do not prove that the model will detect memory leaks reliably in real production applications.

## Intended Use

The model is intended to:

- Support development and testing of the MemoryMedic monitoring pipeline.
- Classify MemoryMedic CSV telemetry as `normal` or `leak`.
- Provide a leak probability that can help a developer decide whether a process requires further investigation.
- Demonstrate process monitoring, feature engineering, model training, evaluation, storage, and prediction in one end-to-end project.

## Out-of-Scope Uses

The model should not be used to:

- Automatically terminate, restart, or modify production processes without human review.
- Make high-stakes availability, security, medical, financial, or safety decisions.
- Claim reliable real-world memory-leak detection based only on the current synthetic evaluation.
- Analyze unsupported operating systems or telemetry formats without additional validation.
- Treat every telemetry row as an independent experiment.

## Inputs and Features

The model accepts a MemoryMedic telemetry CSV. Feature engineering uses raw measurements and values derived from recent behavior.

| Feature | Description |
|---|---|
| `rss_kb` | Resident memory currently used by the process. |
| `virtual_memory_kb` | Virtual memory assigned to the process. |
| `peak_rss_kb` | Highest observed resident-memory value. |
| `threads` | Number of process threads. |
| `rss_growth_kb_s` | Rate of resident-memory growth. |
| `minor_faults_s` | Rate of minor page faults. |
| `major_faults_s` | Rate of major page faults. |
| `rss_delta` | Change in resident memory between observations. |
| `rss_mean_10` | Rolling mean of resident memory over ten observations. |
| `rss_std_10` | Rolling standard deviation of resident memory over ten observations. |
| `vm_to_rss_ratio` | Ratio of virtual memory to resident memory. |
| `fault_ratio` | Relationship between major and minor page-fault activity. |

## Output

For each processed telemetry row, the prediction program produces:

- `ml_leak_probability`: a value from 0 to 1.
- `ml_prediction`: either `normal` or `leak`.

The default decision threshold is 0.50. A probability at or above the threshold is classified as `leak`; a lower probability is classified as `normal`.

## Training Data

The final dataset contained **1,243 telemetry rows from 32 independent workload runs**. Each of the four workload programs was executed eight times.

| Workload | Intended behavior | Label | Independent runs |
|---|---|---:|---:|
| `normal_workload` | Maintains stable memory use. | normal | 8 |
| `cache_growth` | Simulates intentional memory growth caused by caching. | normal | 8 |
| `burst_workload` | Creates temporary bursts in memory use. | normal | 8 |
| `linear_leak` | Repeatedly allocates memory without releasing it. | leak | 8 |

The data is synthetic and controlled. It represents repeated executions of four fixed programs rather than a broad sample of real applications.

## Data Partitioning

Data was split by `run_id` so that all rows from a single execution remained in one partition. This reduces leakage caused by placing highly related rows from the same run in both training and evaluation data.

For each workload, the eight runs were divided into:

- 6 training runs
- 1 validation run
- 1 held-out test run

Across all workloads, this produced 24 training runs, 4 validation runs, and 4 test runs. The current evaluation uses a grouped train/validation/test split; it does not use k-fold cross-validation.

## Model Selection

Two candidate classifiers were compared using validation F1 score.

| Candidate model | Validation F1 |
|---|---:|
| Logistic regression | 0.905 |
| Histogram-based gradient boosting | 1.000 |

Histogram-based gradient boosting was selected because it achieved the higher validation F1 score.

## Held-Out Test Performance

The selected model was evaluated once on **156 rows** from the held-out test runs.

| Metric | Result |
|---|---:|
| Accuracy | 1.000 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 score | 1.000 |
| Average precision | 1.000 |
| ROC AUC | 1.000 |
| False-positive rate | 0.000 |
| False-negative rate | 0.000 |

### Confusion Matrix Counts

| Result | Count |
|---|---:|
| True negatives | 117 |
| False positives | 0 |
| False negatives | 0 |
| True positives | 39 |

These perfect scores should be interpreted cautiously. They show that the model separated the included synthetic test runs, not that it will achieve perfect performance on unfamiliar real applications.

## Prediction Smoke Tests

The saved model was loaded by the prediction program and tested on collected CSV files.

- A `linear_leak` CSV produced leak probabilities of approximately **0.999468** for the displayed rows and was classified as `leak`.
- A `normal_workload` CSV produced leak probabilities of approximately **0.000165** for the displayed rows and was classified as `normal`.

These checks confirm that model loading, feature engineering, probability generation, and label output work together. They are functional smoke tests, not new independent evaluations, because the files came from the existing collected dataset.

## Strengths

- The project implements an end-to-end monitoring and prediction pipeline.
- Runs are kept intact during data partitioning to reduce row-level leakage.
- The training process compares more than one candidate model.
- The saved artifact includes evaluation results, split information, and dependency records.
- Predictions include probabilities rather than only class labels.
- Controlled workloads make the pipeline reproducible and easy to inspect.

## Limitations and Risks

- The dataset is small and contains only 32 independent runs.
- The 1,243 telemetry rows are correlated observations, not 1,243 independent experiments.
- Only one synthetic program represents the `leak` class.
- Training and testing use repeated executions of the same four workload programs.
- Real applications may have memory patterns, allocation strategies, runtimes, and operating conditions not represented here.
- Different hardware, Linux configurations, sampling intervals, and background activity may change feature distributions.
- The current evaluation does not use grouped k-fold cross-validation.
- A false positive could cause unnecessary investigation, while a false negative could allow a real leak to go unnoticed.
- Model confidence values should not be interpreted as guaranteed real-world probabilities without calibration on representative production data.

## Responsible Use

MemoryMedic should be used as a diagnostic aid. A `leak` result should prompt a developer to inspect memory trends, logs, allocation behavior, and application context. It should not automatically trigger destructive remediation. Production deployment should include human review, monitoring for data drift, documented alert thresholds, and a safe response procedure.

## Reproducibility

The model pipeline uses:

- Python 3.14.4
- NumPy 2.5.2
- pandas 3.0.5
- scikit-learn 1.9.0
- joblib 1.6.0
- SciPy 1.18.1

The principal implementation files are:

- `ml/feature_engineering.py`
- `ml/train_model.py`
- `ml/predict_csv.py`
- `ml/requirements.txt`

Each completed training output includes:

- `memorymedic_model.joblib`
- `evaluation.json`
- `splits.csv`
- `requirements-used.txt`
- `COMPLETE.txt`

Generated training artifacts are stored under `artifacts/ml/` and are excluded from Git because they are reproducible output files.

## Recommended Next Steps

1. Collect more independent runs from a wider variety of normal and leaking applications.
2. Add multiple leak patterns, allocation rates, runtimes, and workload sizes.
3. Evaluate with grouped k-fold cross-validation when required.
4. Test on applications that were not used to design the synthetic workloads.
5. Measure false-positive rates on long-running production-like normal workloads.
6. Evaluate performance across different Linux systems and hardware configurations.
7. Measure monitoring overhead, model latency, and probability calibration.
8. Define operational alert thresholds and a human-review process before deployment.

## Conclusion

The selected histogram-based gradient boosting model successfully classified the held-out runs from the current controlled synthetic dataset. The result validates the implemented MemoryMedic pipeline as a prototype. Broader real-world data and additional grouped evaluation are required before the model can be considered reliable for production memory-leak detection.
