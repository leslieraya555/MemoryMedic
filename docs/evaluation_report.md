# MemoryMedic Evaluation Report

**Project:** MemoryMedic

**Author:** Leslie Raya

**Evaluation period:** September 2026

## 1. Evaluation Objective

The purpose of this evaluation was to determine whether MemoryMedic could distinguish a controlled memory leak from several normal memory-use patterns. The evaluation tested the complete pipeline: workload execution, Linux process monitoring, CSV collection, feature engineering, model training, model selection, held-out testing, model storage, and prediction.

This is a preliminary synthetic benchmark. It demonstrates that the implemented pipeline works on the included workloads, but it does not establish performance on unrelated real-world applications.

## 2. Workloads and Labels

Four independently executed workload programs were used:

| Workload | Behavior | Label |
| --- | --- | --- |
| normal_workload | Maintains a stable memory allocation. | normal |
| cache_growth | Simulates intentional growth caused by caching. | normal |
| burst_workload | Creates temporary increases in memory usage. | normal |
| linear_leak | Repeatedly allocates memory without releasing it. | leak |

Each workload contributed eight independent monitoring runs, producing 32 total runs.

## 3. Dataset Summary

The final validated dataset contained:

| Measurement | Value |
| --- | ---: |
| Total telemetry rows | 1,243 |
| Independent runs | 32 |
| Workloads | 4 |
| Runs per workload | 8 |
| Held-out test rows | 156 |

The dataset contains raw process telemetry and labels. Important measurements include resident memory, virtual memory, peak resident memory, thread count, memory-growth rate, page-fault rates, timestamps, and run identifiers.

## 4. Feature Engineering

The feature-engineering program validates the required telemetry columns, converts numeric measurements, replaces invalid values, sorts samples chronologically within each run, and calculates derived features.

The model features are:

- Resident memory
- Virtual memory
- Peak resident memory
- Thread count
- RSS growth rate
- Minor page-fault rate
- Major page-fault rate
- Change in RSS
- Rolling RSS mean
- Rolling RSS standard deviation
- Virtual-to-resident-memory ratio
- Major-fault ratio

All feature calculations are performed separately within each run so rolling measurements do not cross run boundaries.

## 5. Partitioning Method

The data was divided by complete run identifiers instead of individual CSV rows. This prevents measurements from the same experiment from appearing in both training and evaluation data.

For each workload, the eight runs were divided into:

| Partition | Runs per workload | Total runs |
| --- | ---: | ---: |
| Training | 6 | 24 |
| Validation | 1 | 4 |
| Test | 1 | 4 |

The test partition remained separate until the final model was selected. This is a grouped train/validation/test evaluation. It is not k-fold cross-validation.

## 6. Candidate Model Comparison

Two classification approaches were compared on the validation partition:

| Model | Validation F1 |
| --- | ---: |
| Logistic regression | 0.905 |
| Histogram-based gradient boosting | 1.000 |

Histogram-based gradient boosting achieved the stronger validation F1 score and was selected for final evaluation.

## 7. Held-Out Test Results

The selected model was evaluated on 156 held-out telemetry rows:

| Metric | Result |
| --- | ---: |
| Accuracy | 1.000 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 score | 1.000 |
| Average precision | 1.000 |
| ROC AUC | 1.000 |
| False-positive rate | 0.000 |
| False-negative rate | 0.000 |

### Confusion Matrix

| Actual / Predicted | Normal | Leak |
| --- | ---: | ---: |
| Normal | 117 | 0 |
| Leak | 0 | 39 |

The model correctly classified all 117 normal rows and all 39 leak rows in this held-out synthetic test partition.

## 8. Prediction Smoke Tests

The saved model was loaded with the CSV prediction program and tested on collected workload files.

| Input | Observed result |
| --- | --- |
| linear_leak CSV | Recent displayed rows were classified as leak with probabilities near 0.999468. |
| normal_workload CSV | Recent displayed rows were classified as normal with leak probabilities near 0.000165. |

These smoke tests confirmed that model serialization, loading, feature engineering, and CSV prediction work together.

## 9. Reproducibility Outputs

Each completed training run stores:

- The serialized MemoryMedic model
- Evaluation metrics in JSON format
- The run-level partition plan
- The package versions used during training
- A completion marker

Generated training artifacts and full collection directories are intentionally excluded from Git. The source code, dependency list, documentation, and small demonstration CSV files remain version controlled.

## 10. Interpretation

The results show that the selected model can distinguish the included linear leak from the three included normal synthetic patterns. Keeping complete runs together provides a more defensible evaluation than randomly splitting individual telemetry rows.

The perfect held-out score should be interpreted cautiously. The workloads are fixed programs, the dataset is small, and multiple runs from the same four programs are highly related. The test measures performance on additional executions of those programs, not general performance on unfamiliar applications.

## 11. Limitations

- The evaluation contains only 32 independent runs.
- All measurements come from four controlled synthetic programs.
- Only one workload represents the leak class.
- The model has not been evaluated on unrelated production applications.
- The current evaluation uses one grouped split rather than grouped k-fold cross-validation.
- Performance may change with longer sessions, different systems, different compilers, background activity, or different leak patterns.
- Telemetry rows within a run are correlated, so row counts must not be treated as counts of independent experiments.

## 12. Future Evaluation

Future work should:

1. Collect longer runs from a wider variety of applications.
2. Add several independent memory-leak implementations.
3. Include additional normal patterns that may resemble leaks.
4. Use grouped k-fold cross-validation when required.
5. Report variation across folds or repeated grouped evaluations.
6. Measure monitoring overhead and prediction latency.
7. Evaluate false positives on production-like programs.
8. Reserve data from entirely new applications for external validation.

## 13. Conclusion

MemoryMedic successfully completed its preliminary synthetic evaluation. The complete monitoring and machine-learning pipeline operated correctly, histogram-based gradient boosting was selected, and the final grouped test produced an F1 score of 1.000 on 156 held-out rows. The results support continued development while also showing the need for broader real-world validation.
