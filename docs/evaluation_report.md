# MemoryMedic AI 2.0 — Evaluation and Verification Report

**Author:** Leslie Raya

**Project:** MemoryMedic / MemoryMedic AI 2.0

**Report Updated:** November 25, 2026 (documentation revision)

**Report edition:** Consolidated historical evaluation, local and CI software verification, November 25 checks, and browser E2E evidence

**Historical Model Benchmark:** September 2026

**Software Verification:** October–November 25, 2026 (recorded test sessions; see Appendix E)

**Repository:** [MemoryMedic on GitHub](https://github.com/leslieraya555/MemoryMedic)

**Evidence note:** Historical model evaluation and subsequent software verification are reported separately; screenshots supplement, rather than substitute for, reproducible results. November 25 local screenshots show successful frontend checks and a five-test Playwright run. An attempted backend rerun was interrupted, so the historical 13-pass backend result must not be misrepresented as a November 25 verification.

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
- Automated unit, integration, and end-to-end browser testing with GitHub Actions continuous integration.

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
| Historical held-out accuracy | 100% |
| Historical held-out precision | 100% |
| Historical held-out recall | 100% |
| Historical held-out F1-score | 1.000 |
| Original Python regression tests | 21 passed |
| MemoryMedic AI 2.0 backend tests | 13 passed |
| React component tests (Vitest) | 4 passed in the recorded local run |
| Playwright Chromium end-to-end tests | **5 passed in recorded November 17 and November 25 local runs**; isolated test fixture model |
| Frontend lint (Oxlint) | Passed in the recorded local run |
| Frontend production build | Successful |
| API prediction demonstration | Successful |
| GitHub Actions | Successful core, backend, dashboard, and Browser E2E CI runs observed |
| November 25 frontend recheck | Four Vitest tests passed; lint clean; Vite production build successful in supplied screenshot |
| November 25 backend recheck | Interrupted before completion; no new backend pass claimed |
| Combined November 16 local verification screenshot | Captured; included in Appendix C |
| Playwright E2E verification screenshot | Five passing Chromium tests; included in Appendix D |

**Overall assessment:** MemoryMedic AI 2.0 is a functioning research and portfolio prototype with verified components and an integrated monitoring dashboard.

The four Vitest/React Testing Library tests use mocked API responses in a jsdom environment. **Separately**, five Playwright tests execute a real Chromium browser against the actual React frontend and FastAPI service using generated, disposable CSV fixtures and a saved test-only model. The E2E results verify integration, **not** independent machine-learning accuracy.

The perfect historical classification results apply only to the controlled synthetic test dataset. They should not be interpreted as proof of perfect memory-leak detection in unfamiliar production software.

### Evidence provenance and interpretation

| Evidence group | Date / period | Verification unit | What it supports | What it does **not** support |
|---|---|---|---|---|
| Controlled ML benchmark | September 2026 | 32 process executions; 1,243 correlated telemetry rows | Performance on four known synthetic workload programs with grouped holdout testing | Unseen-application accuracy or independent deployment reliability |
| Original C++/Python verification | October 2026 | Linux functional checks and Python regression tests | Collector behavior, validation, training, and inference under test conditions | New independent model generalization evidence |
| API and frontend local checks | October–November 16, 2026 | 13 backend tests; four simulated frontend tests; lint; Vite build | Verified program behavior under configured test cases | End-to-end browser coverage or calibrated probabilities |
| Dashboard workload screenshots | November 2026 | Four locally selected historical workload files | Historical telemetry visualization and example predictions | Continuous live monitoring or production traffic |
| Playwright E2E local run | November 17, 2026 | Five Chromium browser cases using 40-row fixtures for each of four workload types | React/real API integration, real saved-test-model inference, refresh and simulated outage UI | Independent ML generalization, calibrated probability, or production deployment |
| GitHub Actions records | October–November 17, 2026 | Checks configured in each of four workflows | Successful runs observed, including separate Playwright E2E CI | Proof of future passing runs or unconfigured checks |

**Independence matters:** The 156 held-out rows came from only four independent monitoring executions (one per workload implementation). The historical benchmark should not be summarized as 156 independent experiments. The same workload **program types** appeared in training, even though complete process runs were separated. The reported row-level accuracy therefore should not be construed as a robust estimate of performance on new programs.

---

## 1. Evaluation Objectives

The primary objective of this evaluation is to assess the correctness, performance, reproducibility, and integration of the MemoryMedic system.

The evaluation addresses six questions:

1. Can MemoryMedic collect and validate Linux process-memory telemetry?
2. Can its machine-learning classifier distinguish normal memory behaviors from the included synthetic leak behavior?
3. Can the FastAPI backend load the trained model and return predictions?
4. Can the React dashboard retrieve telemetry, visualize memory behavior, and display model predictions?
5. Can the system's components be tested automatically and verified through GitHub Actions?
6. Can the actual React app communicate with FastAPI, return fixture-based model predictions, and handle API failures in a real Chromium browser?

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
| Playwright and Chromium | Exercises the frontend and real backend in an isolated end-to-end browser-test environment |

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
\================ test session starts ================
Collected 13 items
backend/tests/test_main.py          PASSED
backend/tests/test_metrics.py       PASSED
backend/tests/test_predictions.py   PASSED
\================ warnings summary ===================
1 deprecation warning
\============== 13 passed, 1 warning ================
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

The React dashboard was opened locally at:

`http://127.0.0.1:5173`

The FastAPI backend was available at:

`http://127.0.0.1:8001`

The browser screenshots demonstrate that the dashboard successfully displayed historical telemetry and a model prediction.

### 14.1 Observed Normal-Workload Results

| Measurement | Displayed Result |
|---|---:|
| Selected workload | `normal_workload` |
| Samples analyzed | 40 |
| Latest RSS | Approximately 67.1 MiB |
| Virtual memory | Approximately 70.9 MiB |
| Peak RSS | Approximately 67.1 MiB |
| Latest classification | Normal |
| Latest leak probability | Approximately 0.02% |
| Classification threshold | 50% |
| Samples predicted as leaks | 0 |

### 14.2 Interpretation

The demonstrated normal workload produced stable RSS measurements.

The API classified the submitted observations as normal.

The dashboard displayed:

- The classification result.
- The latest leak probability.
- The model threshold.
- The number of observations classified.

This demonstrates functioning communication among the frontend, backend, and saved model under the tested local conditions.

It does not establish an independently measured false-positive rate, real-world accuracy, or probability calibration.

### 14.3 Dashboard Verification Checklist

- [x] React dashboard renders.
- [x] Backend health status appears.
- [x] Historical telemetry loads.
- [x] Memory summary cards display.
- [x] Memory chart displays.
- [x] Recent telemetry table displays.
- [x] Prediction request completes.
- [x] Prediction results display.
- [x] Frontend production build completes.
- [x] Add automated React component and integration tests using Vitest and React Testing Library.
- [x] Add real-browser end-to-end tests with Playwright and Chromium against a running FastAPI backend; five cases passed locally on November 17, 2026, and the separate E2E workflow passed on GitHub Actions.
- [ ] Evaluate dashboard behavior with additional independent workloads.
- [ ] Implement and evaluate live monitoring if required.

### 14.4 Frontend Automated Test Verification (November 16, 2026)

The dashboard includes `frontend/src/App.test.jsx`, `frontend/src/setupTests.js`, and `frontend/vitest.config.js`. Its `package.json` defines `npm test` as `vitest run`.

The four recorded local frontend tests passed. These tests cover:

| Test | Verification target | Recorded result |
|---|---|---|
| Dashboard and telemetry loading | Health status, mocked historical metrics, chart rendering, and summary display | Passed |
| Switching to `linear_leak` | Workload selector triggers the corresponding metrics request | Passed |
| AI prediction request | Prediction button sends a POST request and renders classification and score | Passed |
| Backend error display | Mocked HTTP 503 response produces an accessible error message | Passed |

The four Vitest tests stub `fetch` and mock Recharts components. Consequently, they are **frontend component/integration tests with simulated API data**, not browser-based verification. Five **additional** Playwright tests now cover the actual browser, React UI, and FastAPI integration using disposable synthetic fixtures, as documented in Section 14.5 and Appendix D. The separate historical dashboard screenshots document local examples using collected workload telemetry.

**Run locally from the project root:**

```bash
cd ~/Desktop/MemoryMedic/frontend
npm ci
npm test
npm run lint
npm run build
```

**Recorded local verification:** four Vitest tests passed; Oxlint finished without warnings or errors; the Vite production build completed. This is the recorded result, not a claim that the commands were re-run for this document update.

### 14.5 Playwright Real-Browser End-to-End Verification (November 17, 2026)

An additional Playwright test suite was introduced under `e2e/`. It launches **Chromium**, starts the **actual FastAPI backend** on `127.0.0.1:8011` and the **React/Vite frontend** on `127.0.0.1:5174`, and exercises the application as a browser user would.

A fixture generator (`scripts/prepare_e2e_fixtures.py`) creates **40 synthetic observations per workload** and fits a **disposable logistic-regression test model** under Git-ignored `artifacts/e2e/`. These generated fixtures are deliberately isolated from the historical September benchmark data and trained production-style artifacts. The test model is trained on its fixture rows to verify the application integration; **it is not used to assess generalization or ML accuracy**.

| Browser test | Result | Evidence scope |
|---|---|---|
| Open dashboard and display CSV telemetry | Passed | React renders and receives actual FastAPI metrics |
| Load all four workload selections | Passed | `normal_workload`, `burst_workload`, `cache_growth`, and `linear_leak` load through the actual metrics endpoint |
| Submit prediction request | Passed | Actual prediction API returns 40 predictions using the saved test-only model |
| Refresh historical metrics | Passed | Browser triggers a successful metrics API refresh |
| Display an error for a simulated outage | Passed | Playwright intentionally intercepts only this test's metrics request and returns a synthetic HTTP 503 |

**Observed local result:** 5 passed, 0 failed, 0 flaky, 0 skipped (November 17, 2026). The supplied Playwright HTML report recorded an approximately 21.5-second total run. A dedicated `MemoryMedic Browser E2E CI` workflow also completed successfully on GitHub Actions for the relevant commit. See [Appendix D](#appendix-d-november-17-2026--playwright-end-to-end-verification) for commands, links, screenshot evidence, and limitations.

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

The project has separate workflows for the original system, backend, dashboard, and browser-level E2E integration.

### 16.1 CI Workflows

| Workflow | Primary Responsibility |
|---|---|
| `ci.yml` | C++ builds, Python validation, and shell-script checks |
| `backend-ci.yml` | FastAPI backend syntax and automated tests |
| `frontend-ci.yml` | React dashboard lint, Vitest tests, and production build |
| `playwright-e2e.yml` | Chromium browser testing with actual React and FastAPI servers, isolated fixture data, and uploaded reports |

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

### 16.5 Updated Dashboard CI Evidence (November 16, 2026)

The current `frontend-ci.yml` workflow runs static checks (`npm run lint`), automated frontend tests (`npm test`), a production build (`npm run build`), and output verification. A successful dashboard workflow run was captured and committed as `docs/images/memorymedic-frontend-ci-passed.png`.

![Successful MemoryMedic Dashboard CI run](images/memorymedic-frontend-ci-passed.png)

- [Dashboard CI workflow](https://github.com/leslieraya555/MemoryMedic/actions/workflows/frontend-ci.yml)
- [All GitHub Actions runs](https://github.com/leslieraya555/MemoryMedic/actions)
- [Source test file](../frontend/src/App.test.jsx)

**Evidence scope:** A green CI run supports that the configured tests and build succeeded for the checked commit. It is not a production-deployment certificate or an independent model generalization benchmark. The runner may also report non-failing toolchain/deprecation notices.

### 16.6 Browser E2E CI Evidence (November 17, 2026)

The standalone [browser E2E workflow](../.github/workflows/playwright-e2e.yml) uses Python 3.12 and Node.js 22, installs the backend/ML dependencies, prepares the existing React frontend, installs Playwright Chromium, and runs the isolated E2E suite (`npm test` in `e2e/`). It uploads the HTML report and diagnostic traces as the `memorymedic-playwright-report` artifact, with a 14-day retention configuration.

A successful `MemoryMedic Browser E2E CI` workflow run is visible in the November 17, 2026 GitHub Actions verification screenshot. The workflow checks the browser-to-API integration at a specific revision; **a green result is not a production readiness guarantee**. Documentation-only commits may not trigger this workflow because the trigger's path filters do not include `docs/**`.

- [Browser E2E CI workflow source](../.github/workflows/playwright-e2e.yml)
- [Browser E2E CI runs](https://github.com/leslieraya555/MemoryMedic/actions/workflows/playwright-e2e.yml)

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

### 17.5 Verify Frontend Tests and Lint

```bash
cd ~/Desktop/MemoryMedic/frontend
npm ci
npm test
npm run lint
```

The four automated Vitest frontend tests use mocked APIs and are distinct from the five Playwright real-browser tests. Both suites are retained and run independently in their respective workflows.

### 17.6 Start the API

Only start a new server if port 8001 is available.

```bash
cd ~/Desktop/MemoryMedic
PYTHONPATH=. backend/.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8001
```

The API documentation is available at:

http://127.0.0.1:8001/docs The health endpoint is available at:

http://127.0.0.1:8001/health

### 17.7 Start the Frontend

In a separate terminal:

```bash
cd ~/Desktop/MemoryMedic/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

The dashboard is available at:

http://127.0.0.1:5173 If a port is already occupied by the intended running service, use the existing service rather than starting a duplicate.

### 17.8 Reproduce the Playwright Browser E2E Verification

See the [E2E testing README](../e2e/README.md) for full one-time installation steps. From the repository root, after preparing the isolated Python environment and installing Node dependencies, run:

```bash
cd ~/Desktop/MemoryMedic
cd e2e
MEMORYMEDIC_E2E_PYTHON="$(cd .. && pwd)/artifacts/e2e-venv/bin/python" npm test
npm run report
```

On a new checkout, prepare the E2E environment first:

```bash
cd ~/Desktop/MemoryMedic
python3 -m venv artifacts/e2e-venv
artifacts/e2e-venv/bin/python -m pip install -r ml/requirements.txt -r backend/requirements.txt
(cd frontend && npm ci)
(cd e2e && npm ci && npx playwright install chromium)
```

Playwright manages servers on ports `5174` and `8011` to avoid interference with the conventional development ports (`5173` and `8001`). The test environment variables `MEMORYMEDIC_DATA_ROOT`, `MEMORYMEDIC_MODEL_ROOT`, and `MEMORYMEDIC_API_ORIGIN` direct the application only to E2E fixtures and test services. Source files: [`playwright.config.js`](../e2e/playwright.config.js), [`dashboard.spec.js`](../e2e/tests/dashboard.spec.js), and [`prepare_e2e_fixtures.py`](../scripts/prepare_e2e_fixtures.py).

## 18. Evidence and Verification Records

The checked-in [backend pytest terminal log](memorymedic-terminal-output.txt) records 13 passing tests and one non-failing warning.

The following evidence supports the documented project evaluation.

**November 16 verification artifact:** The combined test screenshot is documented in [Appendix C](#appendix-c-november-16-2026--local-verification-evidence). The file `docs/images/memorymedic-full-test-verification.png` has been committed in the repository and is linked below.

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
| Backend pytest verification screenshot | `docs/images/memorymedic-backend-13-tests-passed.png` |
| Dashboard application | `frontend/src/App.jsx` |
| Frontend automated tests | `frontend/src/App.test.jsx` and `frontend/src/setupTests.js` |
| Frontend test configuration | `frontend/vitest.config.js` |
| Frontend build configuration | `frontend/vite.config.js` |
| Real-browser E2E test suite | `e2e/tests/dashboard.spec.js` |
| Playwright test server configuration | `e2e/playwright.config.js` |
| Isolated fixture generator | `scripts/prepare_e2e_fixtures.py` |
| E2E CI workflow | `.github/workflows/playwright-e2e.yml` |
| CI workflows | `.github/workflows/` |
| Frontend CI pass screenshot | `docs/images/memorymedic-frontend-ci-passed.png` |
| Four workload screenshots | `docs/images/memorymedic-*-prediction.png` (see appendix) |
| Original build screenshot | `docs/images/memorymedic-build-test-training-results.png` |
| Combined local verification screenshot | `docs/images/memorymedic-full-test-verification.png` |
| Playwright Chromium pass screenshot | `docs/images/memorymedic-playwright-e2e-5-tests-passed.png` |
| Historical model evaluations | `artifacts/ml/training_*/evaluation.json` |

### 18.1 Historical Verification Screenshot

![MemoryMedic historical build, testing, and model-training verification](images/memorymedic-build-test-training-results.png)

The image documents historical project build and training verification.

### 18.2 Verified Screenshot Inventory

The following screenshot filenames have been verified in the repository's `docs/images/` directory:

| Screenshot | What it documents |
|---|---|
| [`memorymedic-build-test-training-results.png`](images/memorymedic-build-test-training-results.png) | Earlier local build, testing, and training demonstration |
| [`memorymedic-normal-workload-prediction.png`](images/memorymedic-normal-workload-prediction.png) | Normal-workload dashboard and prediction |
| [`memorymedic-linear-leak-prediction.png`](images/memorymedic-linear-leak-prediction.png) | Linear-leak dashboard and prediction |
| [`memorymedic-memory-burst-prediction.png`](images/memorymedic-memory-burst-prediction.png) | Memory-burst dashboard and prediction |
| [`memorymedic-cache-growth-prediction.png`](images/memorymedic-cache-growth-prediction.png) | Cache-growth dashboard and prediction |
| [`memorymedic-frontend-ci-passed.png`](images/memorymedic-frontend-ci-passed.png) | Successful frontend GitHub Actions verification |
| [`memorymedic-full-test-verification.png`](images/memorymedic-full-test-verification.png) | November 16 local terminal capture of backend tests, Vitest, lint, and Vite build; available in the repository |
| [`memorymedic-backend-13-tests-passed.png`](images/memorymedic-backend-13-tests-passed.png) | Dedicated local pytest screenshot showing 13 passing backend tests and one non-failing warning; added November 17 |
| [`memorymedic-playwright-e2e-5-tests-passed.png`](images/memorymedic-playwright-e2e-5-tests-passed.png) | November 17 Playwright HTML report showing five passing Chromium browser tests |

Additional backend and performance screenshots should be added only after capturing the corresponding evidence. Do not relabel illustrative images as independent benchmark results.

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

### 19.9 E2E Browser Coverage Scope

The Playwright suite currently exercises Chromium only and uses small synthetic fixture datasets (four workload types with 40 samples each), not continuous streaming, realistic multi-user load, or broad browser/device coverage. One error-state test deliberately simulates an API outage. The fitted E2E logistic-regression model is trained on its own fixture rows and must **never** be used to substantiate held-out model performance, calibrated probabilities, or generalization on unfamiliar programs.

### 19.10 Deployment Limitations

The project has been demonstrated in a local development environment.

A production deployment would require additional security, monitoring, operational testing, and reliability engineering.

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

### 20.7 Expand Browser Coverage Beyond the Initial Playwright Suite

**Completed November 17, 2026:** Playwright real-browser E2E tests against a running backend now verify dashboard loading, four workload selections, saved-test-model inference, refresh behavior, and error reporting for a simulated HTTP 503. The original four Vitest mocked-component tests are retained.

**Still recommended:**

- Add Firefox and WebKit browser projects after testing OS and dependency compatibility.
- Add keyboard navigation and accessibility assertions, including screen-reader-oriented semantics.
- Measure large-dataset rendering and response-time characteristics under defined conditions.
- Add more genuine backend failure scenarios and recovery/retry tests without relying only on route interception.
- Check for flaky behavior across repeated runs and preserve reproducible failure traces.
- Add independent application datasets to evaluate model behavior; treat those results separately from fixture-based E2E functionality.

### 20.8 Add Grouped Cross-Validation if Required

If additional model evaluation is required, use grouping that prevents the same run from appearing in multiple folds.

Report fold membership and performance variation while preserving a separate final test partition.

## 21. Future Development Roadmap

| Priority | Development Task | Status |
|---|---|---|
| High | Verify predictions across additional workload types | Further testing needed |
| High | Expand independent benchmark workloads | Planned |
| High | Measure false alarms and detection latency | Planned |
| High | Measure monitoring overhead | Planned |
| Medium | Add real-browser end-to-end integration tests | **Completed November 17, 2026:** five local Playwright tests passed; Browser E2E CI succeeded |
| Medium | Evaluate probability calibration | Planned |
| Medium | Add live process-monitoring integration | Future development |
| Medium | Implement configurable alerting | Future development |
| Low | Optimize frontend bundle size | Future enhancement |
| Low | Prepare a deployment architecture | Future enhancement |

The completed E2E entry documents software-integration coverage; it is not a claim of real-world classifier accuracy. Other entries are future development goals, not completed functionality.

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
- Five Playwright Chromium end-to-end browser tests passed locally, with successful separate Browser E2E CI, using isolated test-only datasets and model artifacts.

The MemoryMedic AI 2.0 dashboard also displayed telemetry and predictions for the normal, linear-leak, memory-burst, and cache-growth synthetic workloads in the recorded local screenshots.

**Conclusion:** MemoryMedic AI 2.0 is a functioning, modular, and tested research/portfolio prototype under the documented conditions.

Its current evaluation provides evidence that the implemented system works on controlled synthetic workloads and selected local demonstrations.

Additional independent benchmarking is required before making strong claims about general-purpose memory-leak detection, real-world reliability, calibrated risk probabilities, or production readiness.

---

## References and Project Documentation

### Project Repository

[MemoryMedic GitHub Repository](https://github.com/leslieraya555/MemoryMedic)

### Source Code

- [Model Training](../ml/train_model.py)
- [Feature Engineering](../ml/feature_engineering.py)
- [Offline Predictions](../ml/predict_csv.py)
- [FastAPI Application](../backend/app/main.py)
- [Prediction API](../backend/app/predictions.py)
- [React Dashboard](../frontend/src/App.jsx)
- [Dashboard Automated Tests](../frontend/src/App.test.jsx)
- [Frontend CI Workflow](../.github/workflows/frontend-ci.yml)
- [Playwright Browser E2E Tests](../e2e/tests/dashboard.spec.js)
- [Playwright Configuration](../e2e/playwright.config.js)
- [Isolated E2E Fixture Generator](../scripts/prepare_e2e_fixtures.py)
- [Browser E2E CI Workflow](../.github/workflows/playwright-e2e.yml)
- [Vite Configuration](../frontend/vite.config.js)

### Related Documentation

- [System Architecture](architecture.md)
- [Model Card](model_card.md)
- [Interview Guide](interview_guide.md)
- [Browser E2E Reproduction Guide](../e2e/README.md)

### Continuous Integration

[MemoryMedic GitHub Actions](https://github.com/leslieraya555/MemoryMedic/actions)

[Historical CI Verification — October 23, 2026](https://github.com/leslieraya555/MemoryMedic/actions/runs/40029177958)

## Appendix A. Dashboard Workload Verification Screenshots

The following screenshots document the MemoryMedic AI 2.0 dashboard using four controlled synthetic workloads.

They provide visual evidence of the historical telemetry display and locally demonstrated prediction behavior.

### A.1 Normal Workload

![Normal workload dashboard and prediction](images/memorymedic-normal-workload-prediction.png)

### A.2 Linear Memory-Leak Workload

![Linear memory-leak dashboard and prediction](images/memorymedic-linear-leak-prediction.png)

### A.3 Memory-Burst Workload

![Memory-burst dashboard and prediction](images/memorymedic-memory-burst-prediction.png)

### A.4 Cache-Growth Workload

![Cache-growth dashboard and prediction](images/memorymedic-cache-growth-prediction.png)

### A.5 Evidence Interpretation

These images demonstrate dashboard functionality on selected synthetic workloads. They do not establish real-world detection accuracy, probability calibration, or production readiness.

---

## Appendix B. Continuous Integration Evidence

### B.1 Successful dashboard workflow

![MemoryMedic dashboard CI passing](images/memorymedic-frontend-ci-passed.png)

This image records the status of a configured GitHub Actions workflow for a specific repository revision. The workflow installs dependencies, performs frontend lint and Vitest checks, builds the dashboard, and checks expected output files. A green workflow badge verifies only the checks run for that revision.

### B.2 Workflow source and results

- [Core C++ and ML CI](https://github.com/leslieraya555/MemoryMedic/actions/workflows/ci.yml)
- [FastAPI backend CI](https://github.com/leslieraya555/MemoryMedic/actions/workflows/backend-ci.yml)
- [Dashboard frontend CI](https://github.com/leslieraya555/MemoryMedic/actions/workflows/frontend-ci.yml)
- [Chromium browser E2E CI](https://github.com/leslieraya555/MemoryMedic/actions/workflows/playwright-e2e.yml)
- [All workflow runs](https://github.com/leslieraya555/MemoryMedic/actions)

### B.3 CI interpretation

Workflow completion is useful reproducibility evidence. Individual workflow logs and the commit SHA should be consulted to determine precisely which checks ran. GitHub Actions do not by themselves establish performance on unfamiliar applications, production security, or real-time monitoring behavior.

---

## Appendix C. November 16, 2026 — Local Verification Evidence

These are **local software verification results** obtained from the project root and `frontend/` directory. They are not a rerun of the September machine-learning benchmark.

### C.1 Backend API tests

**Command (project root):**

```bash
PYTHONPATH=. backend/.venv/bin/python -m pytest backend/tests -v
```

**Recorded summary:**

```text
13 passed, 1 warning
```

The warning is a deprecation notice from FastAPI/Starlette test tooling regarding `TestClient`; it does not indicate a failed backend test. The recorded terminal output is also preserved in [`memorymedic-terminal-output.txt`](memorymedic-terminal-output.txt).

#### Backend Test Verification Screenshot

![MemoryMedic backend — 13 tests passed](images/memorymedic-backend-13-tests-passed.png)

The screenshot documents the successful local verification of the MemoryMedic AI 2.0 FastAPI backend. It was added to the repository on November 17, 2026.

**Recorded results:**

- **Testing framework:** pytest
- **Backend tests collected:** 13
- **Tests passed:** 13
- **Tests failed:** 0
- **Warnings:** 1 non-failing deprecation warning
- **Verification status:** Passed

The tests cover API routes, historical telemetry validation, prediction requests, and error handling. Some tests use fake estimators to isolate API behavior. These results confirm the tested backend behavior under the configured conditions; they do not independently demonstrate machine-learning accuracy or production readiness.

**Evidence file:** [`docs/images/memorymedic-backend-13-tests-passed.png`](images/memorymedic-backend-13-tests-passed.png)

### C.2 React dashboard component tests

**Command (`frontend/`):**

```bash
npm test -- --run
```

**Recorded summary:**

```text
Test Files  1 passed
Tests       4 passed
```

The tests cover dashboard/telemetry rendering, selecting the linear-leak workload, requesting a prediction, and displaying a backend error. The tests mock `fetch` responses and chart components; they do **not** execute a real browser with a live backend.

### C.3 Frontend lint

**Command (`frontend/`):**

```bash
npm run lint
```

**Recorded summary:**

```text
0 warnings
0 errors
```

The linter ran successfully; this is not equivalent to complete security or correctness verification.

### C.4 Frontend production build

**Command (`frontend/`):**

```bash
npm run build
```

**Recorded summary:** The Vite production build completed successfully and generated `frontend/dist/` artifacts. The bundle-size advisory was informational and did not fail the build.

### C.5 Combined visual verification

![MemoryMedic AI 2.0 — backend, frontend, lint, and production build verification](images/memorymedic-full-test-verification.png)

**Evidence file:** `docs/images/memorymedic-full-test-verification.png`

This screenshot captures the four local command summaries above in one VS Code terminal session. It is a convenient visual audit aid; the underlying commands, terminal outputs, source tests, and CI workflow definitions remain the stronger reproducible evidence. Both the PNG and this report are present in the repository, allowing the image to render in GitHub's Markdown preview.

| Verification | Result in the capture | Interpretation |
|---|---|---|
| FastAPI tests | 13 passed, 1 non-failing warning | API behavior passed the implemented test cases |
| Vitest | 4 passed | Mocked dashboard component behavior passed |
| Lint | 0 warnings, 0 errors | Configured static lint checks passed |
| Vite build | Successful | Frontend compilation and asset generation passed |

### C.6 Reproduction in a new local session

From the project root, after setting up the repository's documented Python environment:

```bash
cd ~/Desktop/MemoryMedic
PYTHONPATH=. backend/.venv/bin/python -m pytest backend/tests -v
cd frontend
npm ci
npm test -- --run
npm run lint
npm run build
```

Do not treat the test count alone as a fixed guarantee for future revisions: it can change when tests are added or removed. Review the logs if the expected test count changes.

### C.7 Evidence completeness

The project has historical model results, four example dashboard captures, a preserved backend test log, the dedicated backend verification screenshot, frontend CI evidence, a combined local verification screenshot, **five passing Playwright Chromium E2E tests**, a committed Playwright pass screenshot, and a successful dedicated browser E2E CI workflow. The browser E2E checks are **completed for their stated scope**; remaining research includes independent-application benchmarking, false-alert measurements, detection latency, monitoring overhead, probability calibration, and broader browser/accessibility/performance tests.

---

## Appendix D. November 17, 2026 — Playwright End-to-End Verification

### D.1 Purpose and Evidence Boundary

On November 17, 2026, MemoryMedic AI 2.0 gained a real-browser integration test suite using **Playwright with Chromium**. The suite launches the **actual React/Vite dashboard** and **actual FastAPI backend**, loads disposable CSV telemetry, and calls saved-model inference through the API.

Unlike the four original Vitest component tests, which mock the HTTP layer, four Playwright scenarios use real backend endpoints. **Only the outage test mocks a metrics response**: it intentionally injects HTTP 503 using Playwright route interception to verify the user-facing error state.

This appendix reports **software integration tests only**, not new machine-learning classifier accuracy, calibrated model probabilities, or production readiness.

### D.2 Execution Environment and Test Isolation

| Element | Verified configuration |
|---|---|
| Local verification date | November 17, 2026 |
| Browser testing framework | Playwright Test |
| Browser project | Chromium (`Desktop Chrome` settings) |
| Local frontend | React/Vite at `http://127.0.0.1:5174` |
| Local backend | FastAPI at `http://127.0.0.1:8011` |
| Test source | `e2e/tests/dashboard.spec.js` |
| Test setup | `e2e/playwright.config.js` |
| Synthetic fixture generator | `scripts/prepare_e2e_fixtures.py` |
| Test data | Four CSV files, 40 samples per workload, in Git-ignored `artifacts/e2e/data/` |
| Test-only model | Logistic regression, trained on its fixture rows and saved under Git-ignored `artifacts/e2e/models/` |
| CI workflow | `.github/workflows/playwright-e2e.yml` |

The E2E environment overrides `MEMORYMEDIC_DATA_ROOT`, `MEMORYMEDIC_MODEL_ROOT`, and `MEMORYMEDIC_API_ORIGIN` for the test servers; original development settings remain available. Generated test artifacts are intentionally separated from the historical September benchmark and existing real model artifacts.

### D.3 Results — Five Browser Tests

| # | Playwright test | Recorded result | What it establishes |
|---:|---|---|---|
| 1 | Opens the real dashboard and displays CSV telemetry | Passed | Chromium displays real metrics and the memory chart after loading from FastAPI |
| 2 | Loads all four workloads from the real metrics endpoint | Passed | User selections request the correct API data for all four test workloads |
| 3 | Sends a real prediction request to the saved test model | Passed | A POST to `/api/v1/predict` returns 40 predictions for fixture telemetry and the dashboard displays prediction information |
| 4 | Refreshes historical telemetry via the real API | Passed | Refresh initiates and completes a successful metrics request |
| 5 | Shows an understandable error for a simulated metrics outage | Passed | The UI displays an appropriate error after Playwright intercepts the metrics request and supplies HTTP 503 |

**Local Playwright HTML report summary (November 17, 2026):**

```text
Project: chromium
Tests:   5 passed
Failed:  0
Flaky:   0
Skipped: 0
Total report time: approximately 21.5 seconds
```

These observed counts are evidence for this run and may change if the suite is expanded.

### D.4 Screenshot — Local Browser Verification

![MemoryMedic AI 2.0 — Playwright Chromium: five E2E tests passed](images/memorymedic-playwright-e2e-5-tests-passed.png)

**Evidence file:** [`docs/images/memorymedic-playwright-e2e-5-tests-passed.png`](images/memorymedic-playwright-e2e-5-tests-passed.png)

The screenshot shows the Playwright HTML report's five green test entries. It is useful visual evidence, but the underlying executable test source and GitHub Actions logs are necessary for independently reproducing the results.

### D.5 GitHub Actions Browser CI Verification

The repository contains a separate [MemoryMedic Browser E2E CI workflow](../.github/workflows/playwright-e2e.yml). The November 17, 2026 GitHub Actions screenshot showed a successful **Browser E2E CI** run alongside successful core, backend, and dashboard workflows.

The browser CI workflow checks out the repository, configures Python and Node.js, installs the ML/backend and frontend dependencies, installs Playwright Chromium, executes the suite, and uploads the HTML report and failure traces when available. The report artifact uses a configured **14-day retention period**; temporary report download availability is not guaranteed beyond that setting.

- [Browser E2E CI workflow runs](https://github.com/leslieraya555/MemoryMedic/actions/workflows/playwright-e2e.yml)
- [All MemoryMedic GitHub Actions](https://github.com/leslieraya555/MemoryMedic/actions)

The passing run supports that the configured tests succeeded for the tested commit. It does not prove that future commits will always pass.

### D.6 Reproduce the E2E Tests

**First-time setup (repository root; macOS/Linux with compatible Python/Node.js):**

```bash
cd ~/Desktop/MemoryMedic
python3 -m venv artifacts/e2e-venv
artifacts/e2e-venv/bin/python -m pip install -r ml/requirements.txt -r backend/requirements.txt
(cd frontend && npm ci)
(cd e2e && npm ci && npx playwright install chromium)
```

**Run Chromium E2E tests (repository root):**

```bash
cd ~/Desktop/MemoryMedic
cd e2e
MEMORYMEDIC_E2E_PYTHON="$(cd .. && pwd)/artifacts/e2e-venv/bin/python" npm test
```

**Open the HTML report (from `e2e/`):**

```bash
npm run report
```

Playwright automatically starts and stops the test servers. Ports `5174` and `8011` must be free. The suite creates fresh Git-ignored fixtures for testing. To inspect implementation and troubleshoot platform-specific prerequisites, see [`e2e/README.md`](../e2e/README.md).

### D.7 Interpretation, Limitations, and Next Experiments

**Supported by the recorded evidence:**

- Real Chromium execution of the React app and actual FastAPI endpoints.
- Four workload selections with 40 fixture samples each.
- Model inference through a **test-only saved sklearn estimator**, including the returned 40-row prediction response.
- Telemetry refresh and a separately simulated metrics-outage error state.
- Local five-test pass and successful dedicated GitHub Actions browser E2E verification.

**Not established by these E2E results:**

- Held-out leak-detection accuracy, new-model generalization, or independent classification performance.
- Memory-leak probability calibration or production incident-detection reliability.
- Continuous real-time Linux monitoring, multi-process aggregation, or deployment hardening.
- Performance, resource overhead, error rates under sustained load, or multi-browser compatibility.
- Security, accessibility conformance, or correctness under unfamiliar real-world workloads.

**Next practical experiments:** broaden browser coverage, add accessibility and true backend-recovery assertions, run repeated CI tests to investigate flakiness, and independently benchmark the ML pipeline on **new application implementations and independent monitoring runs**. Preserve the historical model benchmark as a separate experimental result.

## Appendix E. November 25, 2026 — Local Recheck and Documentation Status

### E.1 Evidence and scope

The accompanying November 25, 2026 VS Code screenshots show new local command output following the earlier recorded verification sessions. The report distinguishes completed checks from interrupted commands and does not extrapolate model accuracy from software tests.

| Component | November 25 screenshot evidence | Interpretation |
|---|---|---|
| React component tests | 1 Vitest file passed; 4 tests passed | Existing mocked frontend component behavior passed in the displayed run |
| Frontend lint | `0 warnings`, `0 errors` | The configured linter completed successfully |
| Frontend production build | Vite build completed; bundle-size advisory displayed | Compiled frontend assets successfully; advisory is not a test failure |
| Playwright Chromium browser E2E | `5 passed` in the displayed run | Real browser/UI/API integration worked with isolated synthetic fixtures and the saved **fixture** estimator |
| FastAPI backend rerun | `KeyboardInterrupt`; no completed new test summary | **Inconclusive for November 25**. The historical 13-pass result remains separately recorded in Appendix C |
| Independent memory-leak benchmark | No new independent dataset or result shown | Historical synthetic benchmark figures remain unchanged |

The screenshot dates are evidence of these particular local checks, not a guarantee that identical commands will pass on other machines or commits. The Playwright fixtures are not an independent ML performance dataset.

### E.2 Recommended commands for a fresh local verification

From the Mac checkout, use these commands in the **VS Code Terminal**. The backend test command is a separate verification step and should be rerun to completion before reporting a fresh backend result.

```bash
cd "$HOME/Desktop/MemoryMedic"
PYTHONPATH=. backend/.venv/bin/python -m pytest backend/tests -v
```

Frontend component tests, lint, and build:

```bash
cd "$HOME/Desktop/MemoryMedic/frontend"
npm test
npm run lint
npm run build
```

Browser E2E tests, using the existing isolated Python environment:

```bash
cd "$HOME/Desktop/MemoryMedic"
export MEMORYMEDIC_E2E_PYTHON="$PWD/artifacts/e2e-venv/bin/python"
cd e2e
npm test
npm run report
```

Consult [`e2e/README.md`](../e2e/README.md) if environment setup is missing. The E2E suite owns ports 5174 and 8011; stop unrelated services occupying these ports before rerunning.

### E.3 Evidence preservation and reproducibility

- Preserve the original September benchmark artifacts and the recorded run-level split; do not replace historical performance results with E2E fixture results.
- Retain the recorded November 16 backend test screenshot and the November 17 Playwright HTML-report screenshot in `docs/images/`.
- Do not mark an interrupted backend check as passing. Save a new terminal screenshot only after a complete successful rerun.
- Check the Git commit and the corresponding GitHub Actions run when referencing a CI result.
- Treat the independent benchmark plan as **planned research** until data collection, independent analysis, and verification are complete.

### E.4 Outstanding technical evaluation priorities

1. Evaluate applications not represented by the original four workload implementations.
2. Measure false alerts per monitoring hour, event-level precision/recall, and leak-onset-to-alert latency.
3. Measure CPU, resident memory, and runtime overhead in paired monitored/unmonitored trials.
4. Repeat trials with run-level separation and report variability; distinguish observations from independent executions.
5. Assess probability calibration and broaden cross-browser and accessibility testing before making deployment-readiness claims.

This November 25 addendum describes verified software checks and **uncompleted experiments separately**. It adds no new empirical evidence of production memory-leak detection accuracy.

---

**Report prepared by:** Leslie Raya

**Last updated:** November 25, 2026

**Document:** `docs/evaluation_report.md`

**Status:** Research and portfolio prototype; additional benchmarking required for production claims.
