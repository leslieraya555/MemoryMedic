# MemoryMedic AI 2.0 — Evaluation and Verification Report

**Author:** Leslie Raya

**Project:** MemoryMedic / MemoryMedic AI 2.0

**Last report revision:** November 5, 2026

**Historical Model Benchmark:** September 2026

**Software Verification:** October 23–November 5, 2026

**Repository:** [MemoryMedic on GitHub](https://github.com/leslieraya555/MemoryMedic)

---

## Report Navigation

- [Executive Summary](#executive-summary)
- [3. Dataset and Experimental Design](#3-dataset-and-experimental-design)
- [8. Historical Model Evaluation](#8-historical-model-evaluation)
- [12. MemoryMedic AI 2.0 Backend Testing](#12-memorymedic-ai-20-backend-testing)
- [14. Dashboard Functional Verification](#14-dashboard-functional-verification)
- [17. Reproducibility](#17-reproducibility)
- [18. Evidence and Verification Records](#18-evidence-and-verification-records)
- [19. Limitations and Threats to Validity](#19-limitations-and-threats-to-validity)
- [20. Recommended Future Evaluations](#20-recommended-future-evaluations)
- [22. Final Assessment](#22-final-assessment)

---

## Executive Summary

MemoryMedic is a Linux-based process-memory monitoring and machine-learning system designed to detect patterns associated with abnormal memory growth and potential memory leaks.

The project integrates:

- C++ process monitoring and Linux `/proc` telemetry.

- Automated telemetry collection and CSV validation.

- Python feature engineering and supervised machine learning.

- Model training, evaluation, and serialized model persistence.

- A FastAPI backend with historical telemetry and prediction endpoints.

- A React dashboard with memory visualization and AI predictions.

- Automated testing and GitHub Actions continuous integration.

MemoryMedic AI 2.0 builds on the original C++ monitoring and machine-learning pipeline by adding an interactive API and dashboard.

### Key Verified Results

| Component | Result |
|---|---|
| Historical dataset | 1,243 telemetry observations |
| Independent monitoring runs | 32 |
| Synthetic workload types | 4 |
| Training runs | 24 |
| Validation runs | 4 |
| Held-out test runs | 4 |
| Selected ML model | Histogram-based gradient boosting |
| Historical synthetic held-out accuracy | 100% (156 correlated observations across 4 test runs) |
| Historical held-out precision | 100% |
| Historical held-out recall | 100% |
| Historical held-out F1-score | 1.000 |
| Original Python regression tests | 21 passed |
| MemoryMedic AI 2.0 backend tests | 13 passed |
| Frontend production build | Successful |
| API prediction demonstration | Successful |
| Normal-workload dashboard demo | 40 samples; 0 flagged as leaks (November 5) |
| Linear-leak dashboard demo | 39 samples; 39 flagged as leaks (November 5) |
| Four dashboard workload screenshots | Present in `docs/images/`; outcomes are individual demonstrations |
| GitHub Actions | Successful checks observed |

**Overall assessment:** MemoryMedic AI 2.0 is a functioning research and portfolio prototype with verified components and an integrated monitoring dashboard.

The perfect historical classification results apply only to the controlled synthetic test dataset. They should not be interpreted as proof of perfect memory-leak detection in unfamiliar production software.

---

## 1. Evaluation Objectives

The primary objective of this evaluation is to assess the correctness, performance, reproducibility, and integration of the MemoryMedic system.

The evaluation addresses five questions:

1. Can MemoryMedic collect and validate Linux process-memory telemetry?

2. Can its machine-learning classifier distinguish normal memory behaviors from the included synthetic leak behavior?

3. Can the FastAPI backend load the trained model and return predictions?

4. Can the React dashboard retrieve telemetry, visualize memory behavior, and display model predictions?

5. Can the system's components be tested automatically and verified through GitHub Actions?

The evaluation separates **machine-learning performance** from **software functionality**.

Successful software tests demonstrate that implemented components behave as expected under tested conditions. They do not independently establish the accuracy of a trained machine-learning model.

## 2. System Architecture

MemoryMedic follows a modular architecture separating operating-system monitoring, feature engineering, machine learning, API services, and frontend visualization.

### 2.1 High-Level Architecture

```text

              MEMORYMEDIC AI 2.0

           Process Intelligence System

                 Linux Process

                       |

                       v

              Linux /proc Filesystem

                       |

                       v

                C++ ProcReader

                       |

                       v

               MemoryAnalyzer

                       |

             +---------+---------+

             |                   |

             v                   v

       RiskAssessment      TelemetryLogger

             |                   |

             v                   v

       Risk Information       CSV Dataset

                                 |

                                 v

                         Data Validation

                                 |

                                 v

                       Feature Engineering

                                 |

                                 v

                         Model Training

                                 |

                      +----------+----------+

                      |                     |

                      v                     v

                Evaluation Results    Saved ML Model

                                            |

                                            v

                                       FastAPI

                                            ^

                                            |

                            +---------------+--------------+

                            |                              |

                            v                              v

                     Telemetry API                   Prediction API

                            ^                              ^

                            |                              |

                            +---------------+--------------+

                                            |

                                            v

                                    React Dashboard

                                            |

                      +---------------------+----------------+

                      |                     |                |

                      v                     v                v

                 Memory Charts       AI Predictions     System Status

```

### 2.2 Architectural Responsibilities

| Component | Responsibility |
|---|---|
| Linux `/proc` | Provides process-memory statistics |
| `ProcReader` | Reads memory and process measurements |
| `MemoryAnalyzer` | Calculates memory-growth behavior |
| `RiskAssessment` | Produces rule-based risk information |
| `TelemetryLogger` | Records measurements to CSV |
| `feature_engineering.py` | Validates telemetry and creates ML features |
| `train_model.py` | Trains and evaluates classifiers |
| `predict_csv.py` | Performs offline inference on telemetry |
| FastAPI | Exposes telemetry and prediction endpoints |
| React | Provides the graphical dashboard |
| Recharts | Visualizes historical measurements |
| GitHub Actions | Automates configured validation workflows |

The original monitoring component operates on Linux.

The current React dashboard displays collected historical CSV measurements rather than continuously streaming live measurements from arbitrary processes.

## 3. Dataset and Experimental Design

### 3.1 Synthetic Workload Categories

The historical benchmark uses four controlled workloads.

| Workload | Behavior | Label | Independent Runs |
|---|---|---|---:|
| `normal_workload` | Maintains approximately 64 MiB of memory | Normal | 8 |
| `burst_workload` | Temporarily allocates approximately 256 MiB and releases it | Normal | 8 |
| `cache_growth` | Adds sixteen approximately 8 MiB cache entries before stabilizing | Normal | 8 |
| `linear_leak` | Retains approximately 1 MiB every 500 ms | Leak | 8 |
| **Total** | | | **32** |

The normal, burst, and cache workloads provide examples of legitimate memory behavior.

The linear leak workload provides a controlled positive example of sustained memory retention.

These workloads are useful for prototype validation because their intended behavior is known.

However, they do not cover every memory-allocation pattern found in production applications.

### 3.2 Dataset Summary

| Property | Recorded Value |
|---|---:|
| Total telemetry observations | 1,243 |
| Total independent executions | 32 |
| Workload implementations | 4 |
| Normal workload implementations | 3 |
| Leak workload implementations | 1 |
| Runs per implementation | 8 |

Each monitoring execution has a unique `run_id`.

Measurements from the same execution are treated as a group during dataset partitioning.

### 3.3 Dataset Structure

Collected datasets are organized into completed collection directories.

```text

data/

└── collection_<identifier>/

    ├── raw/

    │   ├── workload_run_01.csv

    │   ├── workload_run_02.csv

    │   └── ...

    ├── logs/

    ├── runs.csv

    └── COMPLETE.txt

```

The directory shown above illustrates the structure. Actual generated filenames depend on the collection.

The collection manifest records information such as run identities, workload labels, sample counts, and durations.

The completion marker identifies a successfully completed collection batch.

## 4. Data Collection and Validation

### 4.1 Collected Telemetry

MemoryMedic collects measurements from Linux process statistics.

Important measurements include:

| Measurement | Description |
|---|---|
| `timestamp_ms` | Measurement timestamp |
| `rss_kb` | Resident memory in kilobytes |
| `virtual_memory_kb` | Virtual memory in kilobytes |
| `peak_rss_kb` | Peak resident memory |
| `threads` | Number of threads |
| `rss_growth_kb_s` | Estimated RSS growth rate |
| `minor_faults_s` | Minor page-fault rate |
| `major_faults_s` | Major page-fault rate |
| `run_id` | Monitoring execution identifier |

These measurements provide inputs for subsequent feature engineering.

### 4.2 Data Validation

The validation pipeline checks for:

- Missing required columns.

- Duplicate column names.

- Invalid or non-finite numerical values.

- Missing or blank run identifiers.

- Duplicate timestamps within a run.

- Invalid memory and thread measurements.

- Inconsistent labels and run identities.

- Collection-manifest inconsistencies.

- Invalid durations or incomplete collections.

Invalid raw measurements are rejected rather than silently replaced with arbitrary values.

This protects the model from certain forms of malformed telemetry and helps preserve the integrity of the original measurements.

**Result:** The historical training pipeline produced a validated dataset containing 1,243 observations from 32 independent monitoring runs.

## 5. Feature Engineering

MemoryMedic uses a causal feature-engineering pipeline.

Features are calculated using the current observation and preceding observations from the same run.

The feature schema is:

`2-strict-per-run`

### 5.1 Model Features

The classifier uses 12 numerical features.

| Feature | Description |
|---|---|
| `rss_kb` | Current resident memory |
| `virtual_memory_kb` | Current virtual-memory size |
| `peak_rss_kb` | Peak resident memory |
| `threads` | Active thread count |
| `rss_growth_kb_s` | Recent estimated RSS growth rate |
| `minor_faults_s` | Minor page-fault rate |
| `major_faults_s` | Major page-fault rate |
| `rss_delta` | Change in RSS since previous observation |
| `rss_mean_10` | Rolling RSS average over up to ten observations |
| `rss_std_10` | Rolling RSS sample standard deviation |
| `vm_to_rss_ratio` | Virtual-to-resident memory ratio |
| `fault_ratio` | Major-fault rate divided by total fault rate |

### 5.2 Feature Calculation

For each run, observations are sorted by timestamp.

The model then calculates derived features.

Examples include:

**RSS difference**

```text

rss_delta =

    current_rss - previous_rss

```

**Virtual-to-resident memory ratio**

```text

vm_to_rss_ratio =

    virtual_memory_kb / rss_kb

```

**Page-fault ratio**

```text

fault_ratio =

    major_faults_s /

    (minor_faults_s + major_faults_s)

```

When total page-fault activity is zero, the defined derived ratio is zero.

Rolling calculations use up to ten observations, not necessarily ten seconds of data.

### 5.3 Data Leakage Prevention

The following fields are excluded from model inputs:

- Run identifiers.

- Workload names.

- Labels.

- Target variables.

- Existing heuristic risk scores.

Features are calculated within their individual runs.

This reduces the risk of accidentally exposing labels or measurements from other executions to the classifier.

## 6. Dataset Partitioning

The historical dataset uses grouped training, validation, and test partitions.

The split preserves complete monitoring executions.

### 6.1 Partition Results

| Partition | Runs | Rows |
|---|---:|---:|
| Training | 24 | 933 |
| Validation | 4 | 154 |
| Test | 4 | 156 |
| **Total** | **32** | **1,243** |

Each workload contributes:

- Six training runs.

- One validation run.

- One test run.

The recorded random seed is `42`.

### 6.2 Partitioning Method

Run-level grouping prevents observations from the same monitoring execution from appearing in both training and testing.

The evaluation follows this procedure:

1. Validate all eligible collected runs.

2. Assign complete runs to training, validation, and test partitions.

3. Train candidate classifiers on the training partition.

4. Select the classifier using validation F1.

5. Refit the selected configuration on training and validation data.

6. Evaluate once on the held-out test partition.

**Important:** This procedure is grouped holdout evaluation. It is not k-fold cross-validation.

## 7. Machine-Learning Models

Two supervised classification models were evaluated.

### 7.1 Logistic Regression

Logistic regression serves as the baseline.

The implementation uses:

- Standardized numerical features.

- Balanced class weights.

- A fixed random seed.

- A maximum iteration limit.

It provides a relatively interpretable baseline for comparing more complex classification models.

### 7.2 Histogram-Based Gradient Boosting

Histogram-based gradient boosting can model nonlinear relationships and interactions among telemetry features.

The historical implementation uses fixed training settings, including:

```text

learning_rate = 0.06

max_iter = 200

max_leaf_nodes = 15

l2_regularization = 1.0

early_stopping = False

random_state = 42

```

### 7.3 Model Selection Results

| Model | Validation F1 | False Positives | False Negatives |
|---|---:|---:|---:|
| Logistic Regression | 0.904762 | 7 | 1 |
| Histogram-Based Gradient Boosting | **1.000000** | **0** | **0** |

The histogram-based gradient boosting classifier achieved the higher validation F1 score.

It was selected for final fitting and evaluation.

**Selected model:** Histogram-Based Gradient Boosting Classifier.

## 8. Historical Model Evaluation

The selected classifier was evaluated on 156 held-out telemetry observations from four independent executions.

The classification threshold was `0.50`.

### 8.1 Evaluation Metrics

| Metric | Result |
|---|---:|
| Accuracy | **1.000** |
| Precision | **1.000** |
| Recall | **1.000** |
| F1-score | **1.000** |
| Average Precision | **1.000** |
| ROC AUC | **1.000** |
| False Positive Rate | **0.000** |
| False Negative Rate | **0.000** |

These scores are taken from the recorded historical synthetic evaluation.

### 8.2 Confusion Matrix

| Actual / Predicted | Normal | Leak |
|---|---:|---:|
| Normal | 117 | 0 |
| Leak | 0 | 39 |

### Confusion Matrix Interpretation

| Classification Outcome | Count |
|---|---:|
| True Negatives | 117 |
| True Positives | 39 |
| False Positives | 0 |
| False Negatives | 0 |

All 156 held-out telemetry observations were classified correctly.

The test partition contained 117 normal observations and 39 leak observations.

### 8.3 Results by Workload

| Workload | Actual Label | Correct Predictions |
|---|---|---:|
| `normal_workload` | Normal | 39/39 |
| `burst_workload` | Normal | 39/39 |
| `cache_growth` | Normal | 39/39 |
| `linear_leak` | Leak | 39/39 |

Each workload's test subset contains observations from one execution.

The observations are correlated. They should not be treated as 156 independent experiments.

### 8.4 Interpretation

The results demonstrate that the model classified all recorded observations in the held-out synthetic test partition correctly.

However:

- Only four independent test executions were evaluated.

- The test programs were already represented by other executions during training.

- Only one leak-style implementation was included.

- The dataset does not establish performance on unrelated real applications.

The historical result supports the feasibility of the implemented prototype, not a claim of universally perfect detection.

## 9. Historical Functional Verification

Additional verification was performed in October 2026.

These checks exercised the original MemoryMedic monitoring and prediction pipeline.

| Test | Recorded Result |
|---|---|
| Linux CMake build | Passed |
| Registered C++ tests | Passed |
| Normal workload CSV generation | Successful |
| Burst workload CSV generation | Successful |
| Cache-growth CSV generation | Successful |
| Linear-leak CSV generation | Successful |
| Normal-workload prediction smoke test | Expected normal classification |
| Burst-workload prediction smoke test | Expected normal classification |
| Cache-growth prediction smoke test | Expected normal classification |
| Linear-leak prediction smoke test | Expected leak classification |
| Python regression suite | 21 passed |

The prediction smoke tests confirmed that a saved model could be loaded and used to classify newly generated demonstration telemetry.

These checks were not a separately designed independent benchmark.

## 10. Original Python Regression Testing

The original regression suite includes 21 test methods.

| Test Category | Tests | Result |
|---|---:|---|
| Feature engineering | 11 | Passed |
| Grouped dataset partitioning | 4 | Passed |
| CSV and dataset validation | 3 | Passed |
| Metrics and model persistence | 3 | Passed |
| **Total** | **21** | **Passed** |

The tests cover behavior including:

- Correct feature calculations.

- Causal rolling features.

- Run-boundary isolation.

- Rejection of invalid measurements.

- Grouped data splitting.

- Reproducibility of partition assignments.

- Model persistence.

- Test-data isolation.

These tests verify implemented behaviors using synthetic fixtures.

No numerical source-code coverage percentage has been established.

## 11. MemoryMedic AI 2.0 Backend Integration

MemoryMedic AI 2.0 introduces a FastAPI application that exposes the monitoring and machine-learning pipeline through HTTP endpoints.

### 11.1 Backend Architecture

```text

backend/

├── app/

│   ├── __init__.py

│   ├── main.py

│   ├── metrics.py

│   └── predictions.py

├── tests/

│   ├── test_main.py

│   ├── test_metrics.py

│   └── test_predictions.py

└── requirements.txt

```

### 11.2 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Retrieve API information |
| GET | `/health` | Check API responsiveness |
| GET | `/api/v1/metrics` | Retrieve historical telemetry |
| POST | `/api/v1/predict` | Generate memory-leak predictions |
| GET | `/docs` | Access Swagger API documentation |

### 11.3 API Verification

The following behaviors were observed during local testing.

| Verification | Result |
|---|---|
| FastAPI documentation loads | Successful |
| Health endpoint responds | Successful |
| Historical metrics endpoint responds | Successful |
| Prediction endpoint returns JSON | Successful |
| Valid prediction request | HTTP 200 |
| Missing required measurements | HTTP 422 |
| Duplicate timestamps | HTTP 422 |
| Missing trained model | HTTP 503 |

### 11.4 Prediction Processing

The prediction endpoint performs the following operations:

1. Receives telemetry measurements.

2. Validates request fields.

3. Converts observations into a pandas DataFrame.

4. Applies the original feature-engineering pipeline.

5. Locates and loads a trusted local trained-model artifact.

6. Verifies the expected feature schema.

7. Generates probabilities using the trained classifier.

8. Applies the saved classification threshold.

9. Returns predictions as JSON.

The returned response includes the model-run identifier, threshold, number of predictions, and individual prediction results.

A missing model produces an error rather than fabricated classification data.

## 12. MemoryMedic AI 2.0 Backend Testing

The updated FastAPI backend was tested locally using `pytest`.

### 12.1 Test Results

```text

================ test session starts ================

Collected 13 items

backend/tests/test_main.py          PASSED

backend/tests/test_metrics.py       PASSED

backend/tests/test_predictions.py   PASSED

================ warnings summary ===================

1 deprecation warning

============== 13 passed, 1 warning ================

```

The output above summarizes the observed test results rather than reproducing the full original terminal log.

### 12.2 Prediction API Tests

The prediction suite checks:

| Test | Expected Result | Observed Result |
|---|---|---|
| Successful inference response | HTTP 200 | Passed |
| Missing required feature | HTTP 422 | Passed |
| Duplicate timestamp | HTTP 422 | Passed |
| Missing saved model | HTTP 503 | Passed |

Some automated tests use a predictable fake estimator to isolate API behavior.

Therefore, these tests establish that the API behaves as expected for those test conditions, not that the actual trained model achieves a new accuracy score.

### 12.3 Testing Conclusion

The 13 passing tests provide evidence that the implemented backend routes, telemetry validation, and prediction-handling behavior work under the tested conditions.

The single deprecation warning does not represent a failed test.

## 13. React Dashboard Implementation

The MemoryMedic AI 2.0 frontend uses React and Vite.

The dashboard communicates with the backend through locally proxied API requests.

### 13.1 Frontend Structure

```text

frontend/

├── public/

├── src/

│   ├── assets/

│   ├── App.jsx

│   ├── App.css

│   ├── index.css

│   └── main.jsx

├── index.html

├── package.json

├── package-lock.json

└── vite.config.js

```

### 13.2 Dashboard Features

The current dashboard provides:

- Backend connectivity status.

- Selection of historical workload data.

- Resident memory summaries.

- Virtual memory summaries.

- Peak resident memory summaries.

- Number of telemetry observations.

- Memory usage visualization.

- Recent telemetry table.

- AI memory-leak predictions.

- Model classification threshold.

- Model-generated leak probabilities.

### 13.3 Historical Telemetry Visualization

The dashboard plots measurements from the selected workload.

The visualized series include:

- Resident memory.

- Virtual memory.

These charts help users inspect trends in the collected process telemetry.

The data represents recorded observations, not an automatically updating live monitor.

## 14. Dashboard Functional Verification

The integrated React dashboard was opened locally at `http://127.0.0.1:5173`, with the FastAPI service available at `http://127.0.0.1:8001`. Screenshots captured November 5, 2026 document the model output and memory charts for controlled, recorded workloads. The dashboard uses historical CSV data rather than a continuous stream of arbitrary live processes.

### 14.1 Verification Procedure

For each named workload:

1. Confirm the API is available by visiting `http://127.0.0.1:8001/health`.
2. Open the dashboard and select the workload under **Data source**.
3. Verify that the chart, sample count, latest RSS, virtual memory, and telemetry table are populated.
4. Click **Run AI prediction** and check that the request completes.
5. Record the classification, last-sample model score, decision threshold, and total samples flagged as leaks.
6. Save the complete dashboard screenshot with the selected workload visible.

This checks the frontend-to-API-to-saved-model path. It is **not** a new independent model benchmark, because these demonstration samples are not established as an untouched held-out evaluation set.

### 14.2 Recorded Normal-Workload Demonstration

| Measurement | Observed dashboard value |
|---|---:|
| Selected workload | `normal_workload` |
| Telemetry samples | 40 |
| Latest RSS | Approximately 67.1 MiB |
| Latest virtual memory | Approximately 70.9 MiB |
| Peak RSS | Approximately 67.1 MiB |
| Latest classification | Normal |
| Latest displayed model leak score | Approximately 0.02% |
| Displayed decision threshold | 50% |
| Samples flagged as leaks | 0 of 40 |

The normal-workload demonstration showed a nearly flat memory curve and returned a normal classification. The displayed 0.02% is a **model score**, not a calibrated estimate of real-world leak probability.

![Normal-workload dashboard showing stable memory and no flagged samples](images/memorymedic-normal-workload-prediction.png)

### 14.3 Recorded Linear-Leak Demonstration

| Measurement | Observed dashboard value |
|---|---:|
| Selected workload | `linear_leak` |
| Telemetry samples | 39 |
| Latest RSS | Approximately 43.3 MiB |
| Latest virtual memory | Approximately 47.5 MiB |
| Peak RSS | Approximately 43.5 MiB |
| Latest classification | Potential leak detected |
| Latest displayed model leak score | Approximately 99.95% |
| Displayed decision threshold | 50% |
| Samples flagged as leaks | 39 of 39 |

The linear-leak demonstration showed steadily increasing resident and virtual memory, and the trained model flagged the 39 displayed observations as leaks. The **99.95% score is not a validated probability that an unfamiliar application has a memory leak**. These are correlated observations from one controlled demonstration, not 39 independent test runs.

![Linear-leak dashboard showing memory growth and flagged telemetry](images/memorymedic-linear-leak-prediction.png)

### 14.4 Other Captured Workloads

Screenshots were also saved and verified in the repository for the memory-burst and cache-growth demonstrations. They document the interface and plotted telemetry. Their precise classification counts and scores are not reproduced here because they have not been separately transcribed from a source-verified results table.

**Memory burst** (a normal-labeled workload with temporary allocation and release):

![Memory-burst dashboard verification screenshot](images/memorymedic-memory-burst-prediction.png)

**Cache growth** (a normal-labeled workload with bounded memory growth):

![Cache-growth dashboard verification screenshot](images/memorymedic-cache-growth-prediction.png)

To complete numerical comparison for these two workloads, record their latest predicted label, leak score, sample count, and number flagged directly from the corresponding screenshot or a fresh local API response. Do not assume their outputs from the filenames or expected workload labels.

### 14.5 Dashboard Verification Checklist

- [x] React dashboard renders locally.
- [x] API connectivity/health information appears.
- [x] Historical telemetry data loads from the backend.
- [x] Memory-summary cards, chart, and recent telemetry table display.
- [x] Prediction requests complete and results appear.
- [x] Normal-workload demonstration observed (40 samples, no alerts).
- [x] Linear-leak demonstration observed (39 samples, all flagged).
- [x] Screenshot files for all four synthetic workload types saved in `docs/images/`.
- [x] Frontend production build completed locally.
- [ ] Record exact classification counts and model scores for the burst and cache screenshots in a structured results table.
- [ ] Add automated browser-based end-to-end tests and error-state tests.
- [ ] Evaluate on additional independent workloads not represented during training.
- [ ] Measure alert latency, false-alert frequency, and monitoring overhead.

### 14.6 Interpretation and Scope

The dashboard demonstrations support an end-to-end integration claim: a locally running frontend retrieved stored process-memory data, plotted it, submitted observations for model inference, and displayed responses. **They do not change or improve the historical 156-row held-out test metrics**, nor do they prove generalization to real production applications. When reporting model performance, use the held-out benchmark in Section 8 and identify demonstration results separately.

## 15. Frontend Production Build

The frontend was verified using Vite's production build command.

### 15.1 Command

From the `frontend` directory:

```bash
npm run build
```

### 15.2 Recorded Outcome

The terminal output demonstrated:

```text

vite building client environment for production...

Modules transformed successfully.

Build completed successfully.

```

The build generated the frontend `dist` directory.

The local build demonstrated that the React application could be bundled for production.

This does not independently verify runtime connectivity or production deployment.

### 15.3 Build Warning

One observed build reported that some chunks exceeded Vite's size warning threshold.

The warning did not prevent compilation.

Possible future improvements include:

- Dynamic imports.

- Route-level or component-level code splitting.

- Reducing large dependencies.

- Separating infrequently used UI modules.

These optimizations remain future performance work unless a separate change verifies them.

## 16. Continuous Integration and GitHub Actions

MemoryMedic uses GitHub Actions to execute automated checks.

The project has separate workflows for the original system, backend, and dashboard.

### 16.1 CI Workflows

| Workflow | Primary Responsibility |
|---|---|
| `ci.yml` | C++ builds, Python validation, and shell-script checks |
| `backend-ci.yml` | FastAPI backend syntax and automated tests |
| `frontend-ci.yml` | React dashboard dependency installation and production build |

### 16.2 Backend CI

The backend workflow:

1. Checks out the repository.

2. Sets up Python.

3. Installs the project dependencies.

4. Checks Python syntax.

5. Executes the backend test suite.

The configured test command is:

```bash
python -m pytest backend/tests -v
```

### 16.3 Frontend CI

The dashboard workflow:

1. Checks out the repository.

2. Sets up Node.js.

3. Installs frontend dependencies.

4. Builds the React application.

5. Verifies the build output.

The frontend workflow includes:

```bash
npm ci
npm run build
test -f dist/index.html
```

### 16.4 Observed CI Results

GitHub Actions screenshots demonstrated successful workflow runs for the MemoryMedic core project, FastAPI integration, and dashboard build.

The backend feature branch was also successfully merged into `main` after its checks passed.

Successful CI execution verifies the checks configured in each workflow.

It does not substitute for independent model benchmarking.

**GitHub Actions:**

https://github.com/leslieraya555/MemoryMedic/actions

## 17. Reproducibility

Reproducibility is an important objective of the MemoryMedic project.

The historical training procedure records dataset identities, partition assignments, model settings, dependencies, and evaluation results.

### 17.1 Historical Training Artifacts

| Artifact | Purpose |
|---|---|
| `evaluation.json` | Stores model evaluation results |
| `splits.csv` | Records training, validation, and test assignments |
| `memorymedic_model.joblib` | Stores the fitted model and metadata |
| `requirements-used.txt` | Records dependency versions |
| `COMPLETE.txt` | Marks completed training output |

Historical training artifacts were recorded locally under:

```text

artifacts/ml/training_<timestamp>_<identifier>/

```

Full generated artifacts are not guaranteed to exist in a fresh GitHub clone.

### 17.2 Historical Environment

The saved historical training reports record:

| Component | Version |
|---|---|
| Python | 3.14.4 |
| NumPy | 2.5.2 |
| pandas | 3.0.5 |
| scikit-learn | 1.9.0 |
| joblib | 1.6.0 |
| SciPy | 1.18.1 |
| threadpoolctl | 3.6.0 |

The GitHub CI environment may use different compatible dependency versions.

Reproducing historical model results exactly requires compatible code, original data, partition assignments, model settings, and dependencies.

### 17.3 Verify Backend Tests

From the project root:

```bash
cd ~/Desktop/MemoryMedic
PYTHONPATH=. backend/.venv/bin/python -m pytest backend/tests -v
```

### 17.4 Verify Frontend Build

```bash
cd ~/Desktop/MemoryMedic/frontend
npm ci
npm run build
```

### 17.5 Start the API

Only start a new server if port 8001 is available.

```bash
cd ~/Desktop/MemoryMedic
backend/.venv/bin/python -m uvicorn backend.app.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8001
```

The API documentation is available at:

http://127.0.0.1:8001/docs

The health endpoint is available at:

http://127.0.0.1:8001/health

### 17.6 Start the Frontend

In a separate terminal:

```bash
cd ~/Desktop/MemoryMedic/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

The dashboard is available at:

http://127.0.0.1:5173

If a port is already occupied by the intended running service, use the existing service rather than starting a duplicate.

### 17.7 Reproduce a New Synthetic Benchmark (Ubuntu/Linux Only)

The following commands reflect the repository's documented collection/training CLI. **Do not run `scripts/collect_dataset.sh` directly in macOS**: the collector requires Linux `/proc` and the compiled Linux executable. The original September experiment and a newly collected benchmark must remain distinct.

Run from the Linux project root (for example, in the configured Ubuntu Multipass instance):

```bash
# Build and run the C++ tests.
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
# Create a Linux Python environment if one has not been prepared.
python3 -m venv "$HOME/memorymedic-ml-venv"
source "$HOME/memorymedic-ml-venv/bin/activate"
python -m pip install -r ml/requirements.txt
# Collect at least five independent runs of each of four workloads.
bash scripts/collect_dataset.sh 5 40
# Validate completed collection manifests, run identities, and data.
python ml/train_model.py --check-only
# Train candidates, select by validation F1, and test the saved fit.
python ml/train_model.py --seed 42 --threshold 0.5
# Run original Python regression tests separately.
python -m unittest discover -s ml/tests -p 'test_*.py' -v
```

**Important:** The five-repetition command requests 20 independent runs in total, not the 32 runs reported in the September benchmark. To reproduce its eight-runs-per-workload experimental size from a fresh Linux environment, use `bash scripts/collect_dataset.sh 8 40` instead. Multiple completed collection batches can also contribute. A new benchmark may yield different row counts and scores, even with the same seed.

The loader reads completed `data/collection_*/raw/*.csv` batches and verifies them against `runs.csv` and `COMPLETE.txt`. Its `--check-only` mode validates inputs and partition feasibility without saving a model. The training command creates a new `artifacts/ml/training_*` directory and does not overwrite an existing experiment.

### 17.8 Preserve Experiment Provenance and Report Results

For each newly trained experiment, retain the exact generated directory and record:

- Source commit (`git rev-parse HEAD`), operating system, Python version, and dependency versions.
- Collection-directory identities, `runs.csv`, `COMPLETE.txt`, and original raw CSV checksums.
- `splits.csv` with complete, non-overlapping `run_id` partitions.
- `evaluation.json`, `memorymedic_model.joblib`, `requirements-used.txt`, and training `COMPLETE.txt`.
- Counts by workload and by train/validation/test partition, model-selection settings, and the saved decision threshold.
- Held-out confusion matrix and accuracy, precision, recall, F1, and any probability-based metrics that are defined for the final test set.
- Clear separation of **test-set results**, **smoke tests**, **dashboard demonstrations**, and **CI pass/fail checks**.

Do not manually replace old historical metrics with new scores unless the training artifacts and independent split records support that update. Do not commit private data, untrusted model binaries, or large raw datasets without reviewing repository storage and privacy implications. A screenshot alone is not sufficient to reproduce a benchmark.

## 18. Evidence and Verification Records

The following evidence supports the documented project evaluation.

| Evidence | Location |
|---|---|
| Original evaluation | `docs/evaluation_report.md` |
| Original architecture | `docs/architecture.md` |
| Machine-learning training | `ml/train_model.py` |
| Feature engineering | `ml/feature_engineering.py` |
| Offline predictions | `ml/predict_csv.py` |
| API application | `backend/app/main.py` |
| Historical metrics API | `backend/app/metrics.py` |
| Prediction API | `backend/app/predictions.py` |
| Backend tests | `backend/tests/` |
| Dashboard application | `frontend/src/App.jsx` |
| Frontend build configuration | `frontend/vite.config.js` |
| CI workflows | `.github/workflows/` |
| Original build screenshot | `docs/images/memorymedic-build-test-training-results.png` |
| Historical model evaluations | `artifacts/ml/training_*/evaluation.json` |

### 18.1 Historical Verification Screenshot

![MemoryMedic historical build, testing, and model-training verification](images/memorymedic-build-test-training-results.png)

The image documents historical project build and training verification.

### 18.2 Confirmed Dashboard Workload Screenshots

The following four PNG files exist on the repository's `main` branch under `docs/images/` as of November 5, 2026. They are linked above in Section 14.

| Workload | Evidence file | What it can demonstrate |
|---|---|---|
| Normal workload | [`memorymedic-normal-workload-prediction.png`](images/memorymedic-normal-workload-prediction.png) | Stable-memory chart and normal prediction |
| Linear leak | [`memorymedic-linear-leak-prediction.png`](images/memorymedic-linear-leak-prediction.png) | Increasing-memory chart and potential-leak prediction |
| Memory burst | [`memorymedic-memory-burst-prediction.png`](images/memorymedic-memory-burst-prediction.png) | Burst workload dashboard state; inspect outcome before reporting numerical performance |
| Cache growth | [`memorymedic-cache-growth-prediction.png`](images/memorymedic-cache-growth-prediction.png) | Cache workload dashboard state; inspect outcome before reporting numerical performance |

The original historical verification screenshot is retained separately in Section 18.1. An image being present does not, by itself, prove a model score or establish a correctly classified workload.

### 18.3 Additional Recommended Evidence (Not Yet Established in This Report)

- A dated full backend test log tied to a commit hash.
- A dated Vite build log tied to the same commit hash.
- Links to specific successful GitHub Actions workflow runs for that commit.
- A machine-readable JSON or CSV summary of the four dashboard demonstrations, including exact counts and model scores.
- Measured monitor CPU/RAM overhead, detection latency, and false alerts per hour on independent applications.

Only add filenames or numerical claims after the corresponding evidence has been captured and verified. Do not use placeholder screenshots in a published report.

## 19. Limitations and Threats to Validity

MemoryMedic currently has several important limitations.

### 19.1 Limited Synthetic Workloads

The original benchmark uses four controlled applications.

These workloads do not represent the full range of memory behavior found in real-world applications.

### 19.2 Limited Leak Diversity

Only one synthetic leak-style implementation is included in the historical benchmark.

Different leak rates, allocation patterns, and application architectures may require additional training examples.

### 19.3 Small Independent Test Set

Although the test dataset contains 156 observations, only four independent monitoring runs were held out.

Adjacent observations are correlated.

Therefore, the number of independent experimental units is much smaller than the number of rows.

### 19.4 Unknown Real-World Generalization

The historical model has not been independently evaluated on a broad collection of unrelated production applications.

Its real-world precision, recall, and false-alarm rates remain unknown.

### 19.5 Historical Dashboard Data

The current dashboard displays historical CSV observations.

It is not yet a general-purpose live process-monitoring platform.

### 19.6 No Measured Operational Overhead

The available report does not establish:

- CPU overhead from monitoring.

- Memory overhead from monitoring.

- End-to-end detection latency.

- False alerts per monitoring hour.

- Production service reliability.

### 19.7 Limited Cross-Validation

The documented historical model evaluation uses grouped training, validation, and holdout partitions.

Grouped k-fold cross-validation has not been reported.

### 19.8 Probability Calibration

The displayed probability is a model output.

A 0.02% reported leak probability does not establish that the real-world probability of a memory leak is exactly 0.02%.

Probability calibration has not been independently demonstrated.

### 19.9 Deployment Limitations

The project has been demonstrated in a local development environment.

A production deployment would require additional security, monitoring, operational testing, and reliability engineering.

### 19.10 Dashboard Demonstrations Are Not an Independent Test Set

The dashboard's 40 normal and 39 linear-leak predictions represent individual local demonstrations over correlated, historical samples. They should not be pooled with the September benchmark, treated as independent trial counts, or used to claim improved sensitivity and specificity. The cache and burst screenshot files are evidence of a tested interface, but their numeric outcomes are not restated without additional verification.

### 19.11 Reproducibility Depends on Preserved Raw Artifacts

The public repository documents how to collect and train, but raw collections and trained artifacts are not guaranteed to be available in a new clone. Results should be compared only with documented code revisions, complete datasets, hashes, splits, dependency versions, and model artifacts.

## 20. Recommended Future Evaluations

The next stage should focus on testing MemoryMedic beyond its original controlled benchmark.

### 20.1 Expand Workload Diversity

Add independent workloads representing:

- Slow memory leaks.

- Rapid memory leaks.

- Temporary high-memory usage.

- Long-running bounded caches.

- Periodic allocation and release.

- Multithreaded memory activity.

- Unfamiliar applications with different allocation patterns.

### 20.2 Evaluate Unseen Applications

Introduce applications not represented during training.

Preserve a final independent test set while selecting models and thresholds.

### 20.3 Evaluate False Positives

Measure how often normal applications are incorrectly classified as leaks.

Recommended metrics include:

- False positives per independent run.

- False alerts per monitoring hour.

- Specificity.

- Precision.

### 20.4 Measure Detection Latency

Record the time between the beginning of a controlled leak and its detection.

Compare detection performance across multiple leak rates.

### 20.5 Measure Monitoring Overhead

Compare monitored and unmonitored runs under similar conditions.

Record:

- CPU utilization.

- Memory utilization.

- Execution time.

- Monitoring resource consumption.

### 20.6 Evaluate Model Robustness

Test variations in:

- Sample intervals.

- Run durations.

- Memory-allocation rates.

- Application workloads.

- Operating conditions.

### 20.7 Add Frontend Integration Tests

Automate checks for:

- Dashboard loading.

- API connectivity.

- Workload selection.

- Memory visualization.

- Prediction requests.

- Error and loading states.

### 20.8 Add Grouped Cross-Validation if Required

If additional model evaluation is required, use grouping that prevents the same run from appearing in multiple folds.

Report fold membership and performance variation while preserving a separate final test partition.

## 21. Future Development Roadmap

| Priority | Development Task | Status |
|---|---|---|
| High | Capture exact burst/cache prediction counts; evaluate independent workloads | In progress — four dashboard screenshots captured |
| High | Expand independent benchmark workloads | Planned |
| High | Measure false alarms and detection latency | Planned |
| High | Measure monitoring overhead | Planned |
| Medium | Implement browser-based integration tests | Planned |
| Medium | Evaluate probability calibration | Planned |
| Medium | Add live process-monitoring integration | Future development |
| Medium | Implement configurable alerting | Future development |
| Low | Optimize frontend bundle size | Future enhancement |
| Low | Prepare a deployment architecture | Future enhancement |

These are development goals, not claims of completed functionality.

## 22. Final Assessment

MemoryMedic successfully demonstrates an integrated software pipeline combining operating-system process monitoring, machine-learning classification, backend services, automated testing, and interactive data visualization.

The historical benchmark achieved the following results:

- 1,243 telemetry observations.

- 32 independent monitoring runs.

- Four synthetic workload implementations.

- A grouped train/validation/test split.

- Histogram-based gradient boosting selected by validation F1.

- Perfect classification of the 156 held-out synthetic test observations.

Subsequent software verification demonstrated:

- Successful C++ and Python component testing.

- Functional saved-model inference.

- Successful FastAPI integration.

- 13 passing backend tests.

- Successful React dashboard rendering.

- Successful frontend production builds.

- Successful configured GitHub Actions checks.

The MemoryMedic AI 2.0 dashboard also displayed and classified the normal and linear-leak demonstration datasets. It stored screenshots for all four synthetic workloads; exact cache and burst prediction results still require a structured verification record.

**Conclusion:** MemoryMedic AI 2.0 is a functioning, modular, and tested research/portfolio prototype under the documented conditions.

Its current evaluation provides evidence that the implemented system works on controlled synthetic workloads and selected local demonstrations.

Additional independent benchmarking is required before making strong claims about general-purpose memory-leak detection, real-world reliability, calibrated risk probabilities, or production readiness.

---

# References and Project Documentation

## Project Repository

[MemoryMedic GitHub Repository](https://github.com/leslieraya555/MemoryMedic)

## Source Code

- [Model Training](../ml/train_model.py)

- [Feature Engineering](../ml/feature_engineering.py)

- [Offline Predictions](../ml/predict_csv.py)

- [FastAPI Application](../backend/app/main.py)

- [Prediction API](../backend/app/predictions.py)

- [React Dashboard](../frontend/src/App.jsx)

- [Vite Configuration](../frontend/vite.config.js)

## Related Documentation

- [System Architecture](architecture.md)

- [Model Card](model_card.md)

- [Interview Guide](interview_guide.md)

## Continuous Integration

[MemoryMedic GitHub Actions](https://github.com/leslieraya555/MemoryMedic/actions)

[Historical CI Verification — October 23, 2026](https://github.com/leslieraya555/MemoryMedic/actions/runs/40029177958)

---

**Report Prepared By:** Leslie Raya

**Project:** MemoryMedic AI 2.0

**Last Updated:** November 5, 2026

**Document:** `docs/evaluation_report.md`

**End of Evaluation Report**
