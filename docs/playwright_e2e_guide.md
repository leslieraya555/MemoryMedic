# MemoryMedic AI 2.0 — Complete Playwright E2E installation guide

This guide documents **all new files in full**. All snippets are based on the
MemoryMedic GitHub repository inspected November 17, 2026.

**Scope:** real Chromium, real React/Vite, real FastAPI metrics and prediction
endpoints. The locally generated saved sklearn model is deliberately **test
fixture only**, not evidence of generalization or production accuracy.

## Safest setup: download ZIP, add files without overwriting existing ones

1. Download `MemoryMedic_Playwright_E2E_Kit.zip` into your Mac's Downloads folder.
2. In VS Code Terminal, paste these commands:

```bash
cd ~/Desktop/MemoryMedic || exit 1
unzip -n "$HOME/Downloads/MemoryMedic_Playwright_E2E_Kit.zip" -d .
python3 scripts/apply_playwright_e2e.py
python3 -m py_compile scripts/prepare_e2e_fixtures.py

git diff --check
git status --short
```

`unzip -n` skips files that already exist. The patch script **only** adjusts
`backend/app/metrics.py`, `backend/app/predictions.py`, and `frontend/vite.config.js`.
It backs up the original versions under ignored `artifacts/e2e-backups/`.
The working Vitest tests, frontend CI, backend CI and C++ CI are untouched.

## Install Python and browser dependencies

```bash
cd ~/Desktop/MemoryMedic

# Independent venv, stored under the gitignored artifacts/ folder:
python3 -m venv artifacts/e2e-venv
artifacts/e2e-venv/bin/python -m pip install --upgrade pip
artifacts/e2e-venv/bin/python -m pip install -r ml/requirements.txt -r backend/requirements.txt

# Keep the existing frontend dependencies intact:
cd frontend
npm ci
cd ..

# Install Playwright only in the separate e2e directory, creating its lockfile:
cd e2e
npm install --save-dev @playwright/test
npx playwright install chromium
cd ..
```

**Important:** `npm install` creates `e2e/package-lock.json`. Commit it, or
`npm ci` will fail in GitHub Actions.

## Run the five real-browser tests

```bash
cd ~/Desktop/MemoryMedic
export MEMORYMEDIC_E2E_PYTHON="$PWD/artifacts/e2e-venv/bin/python"
cd e2e
npm test
npm run report
```

Playwright starts both temporary servers automatically:
- React/Vite `http://127.0.0.1:5174`
- FastAPI `http://127.0.0.1:8011`

If either port is in use, stop the conflicting process first. The normal
development ports 5173/8001 are not used by these browser tests.

Expected (only after running successfully): five Playwright tests pass.
The two passing screenshot attachments are in the HTML report. Failures
create screenshots, videos and traces under `e2e/test-results/`.

## Re-run existing tests unchanged

```bash
cd ~/Desktop/MemoryMedic
PYTHONPATH=. artifacts/e2e-venv/bin/python -m pytest backend/tests -v
cd frontend
npm test
npm run lint
npm run build
```

## Review and commit *only* the intended files

```bash
cd ~/Desktop/MemoryMedic
git status --short
git diff --check

git add backend/app/metrics.py backend/app/predictions.py frontend/vite.config.js \
        scripts/prepare_e2e_fixtures.py scripts/apply_playwright_e2e.py \
        e2e/ .github/workflows/playwright-e2e.yml

git diff --cached --check
git diff --cached --stat
git commit -m "test: add isolated Playwright browser E2E suite"
git push origin main
```

Visit https://github.com/leslieraya555/MemoryMedic/actions and open the
**MemoryMedic Browser E2E CI** run. It should install Python, npm dependencies,
Chromium, start the test API and frontend, run the five tests, and upload the
HTML report. A green check is valid evidence of integration tests, **not of
memory-leak detection quality on unseen programs**.

## Source links

- Playwright webServer: https://playwright.dev/docs/test-webserver
- Playwright CI: https://playwright.dev/docs/ci
- Playwright browser installation: https://playwright.dev/docs/browsers
- Repository: https://github.com/leslieraya555/MemoryMedic

---

## Full new file contents (copy into the indicated path if installing manually)


### `e2e/package.json`

```json
{
  "name": "memorymedic-playwright-e2e",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "playwright test",
    "test:headed": "playwright test --headed",
    "test:ui": "playwright test --ui",
    "report": "playwright show-report"
  }
}
```


### `e2e/.gitignore`

```gitignore
node_modules/
playwright-report/
test-results/
.env
```


### `e2e/playwright.config.js`

```js
// MemoryMedic AI 2.0 — isolated, real-browser integration testing.
// Run from the e2e directory: npm test
import { defineConfig, devices } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const e2eDir = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(e2eDir, '..')
const frontendRoot = path.join(projectRoot, 'frontend')
const fixtureRoot = path.join(projectRoot, 'artifacts', 'e2e')
const backendPython = process.env.MEMORYMEDIC_E2E_PYTHON || 'python3'
const backendURL = 'http://127.0.0.1:8011'
const frontendURL = 'http://127.0.0.1:5174'

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: frontendURL,
    ...devices['Desktop Chrome'],
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
  webServer: [
    {
      name: 'FastAPI + isolated e2e fixtures',
      // Generate disposable telemetry and a disposable sklearn model before serving.
      command: `"${backendPython}" scripts/prepare_e2e_fixtures.py && "${backendPython}" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8011`,
      cwd: projectRoot,
      url: `${backendURL}/health`,
      timeout: 120_000,
      reuseExistingServer: false,
      env: {
        ...process.env,
        PYTHONPATH: projectRoot,
        MEMORYMEDIC_DATA_ROOT: path.join(fixtureRoot, 'data'),
        MEMORYMEDIC_MODEL_ROOT: path.join(fixtureRoot, 'models'),
      },
    },
    {
      name: 'Vite dashboard',
      command: 'npm run dev -- --host 127.0.0.1 --port 5174 --strictPort',
      cwd: frontendRoot,
      url: frontendURL,
      timeout: 120_000,
      reuseExistingServer: false,
      env: {
        ...process.env,
        MEMORYMEDIC_API_ORIGIN: backendURL,
      },
    },
  ],
})
```


### `e2e/tests/dashboard.spec.js`

```js
// MemoryMedic AI 2.0 — real Chromium + React + FastAPI checks.
// Normal cases use the REAL FastAPI endpoints and a disposable saved sklearn model.
// Only the last test intentionally simulates an HTTP outage in the browser.
import { expect, test } from '@playwright/test'

const workloads = [
  ['normal_workload', 'Normal workload'],
  ['burst_workload', 'Memory burst'],
  ['cache_growth', 'Cache growth'],
  ['linear_leak', 'Linear memory leak'],
]

function sampleCount(page) {
  return page.locator('.metric-card').filter({ hasText: 'Samples loaded' }).locator('strong')
}

function selectedWorkload(page) {
  return page.locator('.detail-row').filter({ hasText: 'Workload' }).locator('b')
}

test('opens the real dashboard and displays CSV telemetry', async ({ page }, testInfo) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Memory intelligence dashboard' })).toBeVisible()
  await expect(page.getByText('API connected')).toBeVisible()
  await expect(page.getByLabel('Data source')).toHaveValue('normal_workload')
  await expect(sampleCount(page)).toHaveText('40')
  await expect(selectedWorkload(page)).toHaveText('normal_workload')
  await expect(page.getByRole('heading', { name: 'Memory usage over samples' })).toBeVisible()
  await expect(page.locator('.recharts-surface').first()).toBeVisible()

  await testInfo.attach('normal-workload-dashboard', {
    body: await page.screenshot({ fullPage: true }),
    contentType: 'image/png',
  })
})

test('loads all four workloads from the real metrics endpoint', async ({ page }) => {
  await page.goto('/')
  await expect(sampleCount(page)).toHaveText('40')

  for (const [value] of workloads) {
    if (value !== 'normal_workload') {
      const nextResponse = page.waitForResponse((response) => {
        const url = new URL(response.url())
        return url.pathname === '/api/v1/metrics' &&
          url.searchParams.get('workload') === value && response.status() === 200
      })
      await page.getByLabel('Data source').selectOption(value)
      await nextResponse
    }
    await expect(page.getByLabel('Data source')).toHaveValue(value)
    await expect(selectedWorkload(page)).toHaveText(value)
    await expect(sampleCount(page)).toHaveText('40')
  }
})

test('sends a real prediction request to the saved test model', async ({ page }, testInfo) => {
  await page.goto('/')
  await expect(sampleCount(page)).toHaveText('40')
  await page.getByLabel('Data source').selectOption('linear_leak')
  await expect(selectedWorkload(page)).toHaveText('linear_leak')
  await expect(sampleCount(page)).toHaveText('40')

  const responsePromise = page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/api/v1/predict' &&
    response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Run AI prediction' }).click()
  const response = await responsePromise
  expect(response.status()).toBe(200)

  const body = await response.json()
  expect(body.count).toBe(40)
  expect(body.predictions).toHaveLength(40)
  expect(body.predictions.every((row) => row.leak_probability >= 0 && row.leak_probability <= 1)).toBe(true)
  await expect(page.getByText('Latest leak probability')).toBeVisible()
  await expect(page.getByText('Model threshold')).toBeVisible()
  await expect(page.locator('.prediction-content p')).toContainText('The model classified 40 samples')

  await testInfo.attach('prediction-dashboard', {
    body: await page.screenshot({ fullPage: true }),
    contentType: 'image/png',
  })
})

test('refreshes historical telemetry via the real API', async ({ page }) => {
  await page.goto('/')
  await expect(sampleCount(page)).toHaveText('40')
  const nextResponse = page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/api/v1/metrics' && response.status() === 200,
  )
  await page.getByRole('button', { name: 'Refresh data' }).click()
  await nextResponse
  await expect(sampleCount(page)).toHaveText('40')
  await expect(page.getByText('API connected')).toBeVisible()
})

test('shows an understandable error for a simulated metrics outage', async ({ page }) => {
  await page.route('**/api/v1/metrics?**', (route) => route.fulfill({
    status: 503,
    contentType: 'application/json',
    body: JSON.stringify({ detail: 'E2E simulated metrics outage' }),
  }))
  await page.goto('/')
  await expect(page.getByRole('alert')).toContainText('E2E simulated metrics outage')
  await expect(page.getByText('API unavailable')).toBeVisible()
})
```


### `scripts/prepare_e2e_fixtures.py`

```python
"""Generate disposable integration-test CSVs and sklearn model.

The fixture lives under artifacts/e2e/ (gitignored), never under the real
training artifact or collected dataset locations. It is NOT benchmark data.
Run from the project root: python3 scripts/prepare_e2e_fixtures.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.feature_engineering import MODEL_FEATURES, add_features  # noqa: E402

FIXTURE_ROOT = ROOT / "artifacts" / "e2e"
CSV_ROOT = FIXTURE_ROOT / "data" / "demo_e2e"
MODEL_DIR = FIXTURE_ROOT / "models" / "training_e2e_fixture"

FIELDS = [
    "timestamp_ms", "rss_kb", "virtual_memory_kb", "peak_rss_kb", "threads",
    "rss_growth_kb_s", "minor_faults_s", "major_faults_s", "run_id", "label",
]


def create_samples(workload: str) -> list[dict]:
    rows = []
    previous = None
    peak = 0
    for i in range(40):
        if workload == "normal_workload":
            rss = 62_000 + (i % 4) * 15
        elif workload == "burst_workload":
            rss = 62_000 + (18_000 if i % 10 >= 7 else 0)
        elif workload == "cache_growth":
            rss = 62_000 + min(i, 25) * 140
        elif workload == "linear_leak":
            rss = 62_000 + i * 1_200
        else:
            raise ValueError(f"Unknown fixture workload: {workload}")
        peak = max(peak, rss)
        rows.append({
            "timestamp_ms": 1_730_000_000_000 + i * 1000,
            "rss_kb": rss,
            "virtual_memory_kb": rss + 6_000,
            "peak_rss_kb": peak,
            "threads": 1,
            "rss_growth_kb_s": 0.0 if previous is None else float(rss - previous),
            "minor_faults_s": 1.0 + (i % 3) * 0.25,
            "major_faults_s": 0.0,
            "run_id": f"e2e-{workload}",
            "label": "leak" if workload == "linear_leak" else "normal",
        })
        previous = rss
    return rows


def main() -> None:
    CSV_ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = []

    for workload in ("normal_workload", "burst_workload", "cache_growth", "linear_leak"):
        rows = create_samples(workload)
        with (CSV_ROOT / f"{workload}.csv").open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        all_rows.extend(rows)

    data = add_features(pd.DataFrame(all_rows))
    target = data["label"].eq("leak").astype(int)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=42))
    model.fit(data[MODEL_FEATURES], target)
    artifact = {
        "model": model,
        "features": list(MODEL_FEATURES),
        "threshold": 0.5,
        "fixture_only": True,
    }
    joblib.dump(artifact, MODEL_DIR / "memorymedic_model.joblib")

    (FIXTURE_ROOT / "NOTICE.json").write_text(json.dumps({
        "purpose": "Disposable E2E integration fixture only; not model-quality evidence",
        "workload_count": 4,
        "samples_per_workload": 40,
        "model": "LogisticRegression trained on the same synthetic fixture rows",
        "never_use_for": ["held-out accuracy", "production deployment", "benchmark comparisons"],
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Created E2E-only fixtures under {FIXTURE_ROOT}")
    print("40 samples per workload; separate saved test model; not a benchmark.")


if __name__ == "__main__":
    main()
```


### `scripts/apply_playwright_e2e.py`

```python
"""Non-destructively add environment overrides needed by isolated E2E.

Runs only against the current repo's known FastAPI and Vite source patterns.
Does not alter or overwrite any existing tests or GitHub Actions workflows.
Backs up changed files under artifacts/e2e-backups/ (already gitignored).
Re-running is safe; unexpected source changes abort with a clear error.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "artifacts" / "e2e-backups"


def patch(relative: str, transformations: list[tuple[str, str, int]]) -> None:
    path = ROOT / relative
    original = path.read_text(encoding="utf-8")
    updated = original
    for old, new, required in transformations:
        if new in updated:
            continue
        count = updated.count(old)
        if count != required:
            raise SystemExit(
                f"ABORT: Unexpected source in {relative}. Expected {required} occurrences "
                f"of {old!r}, found {count}. No changes written to this file."
            )
        updated = updated.replace(old, new)

    if updated != original:
        backup = BACKUP / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
        path.write_text(updated, encoding="utf-8")
        print(f"Updated {relative} (original backed up to {backup.relative_to(ROOT)})")
    else:
        print(f"Already configured: {relative}")


def main() -> None:
    patch("backend/app/metrics.py", [
        ("import csv\nimport math", "import csv\nimport os\nimport math", 1),
        ('DATA_ROOT = PROJECT_ROOT / "data"',
         'DATA_ROOT = Path(os.environ.get("MEMORYMEDIC_DATA_ROOT", str(PROJECT_ROOT / "data")))', 1),
    ])
    patch("backend/app/predictions.py", [
        ("from functools import lru_cache\nimport math", "from functools import lru_cache\nimport math\nimport os", 1),
        ('MODEL_ROOT = PROJECT_ROOT / "artifacts" / "ml"',
         'MODEL_ROOT = Path(os.environ.get("MEMORYMEDIC_MODEL_ROOT", str(PROJECT_ROOT / "artifacts" / "ml")))', 1),
    ])
    patch("frontend/vite.config.js", [
        ("import react from '@vitejs/plugin-react'\n",
         "import react from '@vitejs/plugin-react'\n\nconst backendTarget = process.env.MEMORYMEDIC_API_ORIGIN || 'http://127.0.0.1:8001'\n", 1),
        ("target: 'http://127.0.0.1:8001',", "target: backendTarget,", 2),
    ])
    print("Ready. The original API defaults remain 8001 and existing tests are untouched.")


if __name__ == "__main__":
    main()
```


### `.github/workflows/playwright-e2e.yml`

```yaml
name: MemoryMedic Browser E2E CI

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - 'backend/**'
      - 'ml/**'
      - 'e2e/**'
      - 'scripts/prepare_e2e_fixtures.py'
      - '.github/workflows/playwright-e2e.yml'
  pull_request:
    branches: [main]
    paths:
      - 'frontend/**'
      - 'backend/**'
      - 'ml/**'
      - 'e2e/**'
      - 'scripts/prepare_e2e_fixtures.py'
      - '.github/workflows/playwright-e2e.yml'
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: memorymedic-browser-e2e-${{ github.ref }}
  cancel-in-progress: true

jobs:
  browser-e2e:
    name: Chromium + React + FastAPI E2E
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
          cache-dependency-path: |
            backend/requirements.txt
            ml/requirements.txt

      - name: Install API and model dependencies
        run: |
          python -m pip install -r ml/requirements.txt -r backend/requirements.txt
          python -c "import fastapi, uvicorn, sklearn, joblib, pandas"

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: |
            frontend/package-lock.json
            e2e/package-lock.json

      - name: Install existing frontend dependencies
        working-directory: frontend
        run: npm ci

      - name: Install isolated Playwright dependencies
        working-directory: e2e
        run: npm ci

      - name: Install Chromium and system dependencies
        working-directory: e2e
        run: npx playwright install --with-deps chromium

      - name: Run real-browser integration tests
        working-directory: e2e
        env:
          CI: 'true'
          MEMORYMEDIC_E2E_PYTHON: python
        run: npm test

      - name: Upload Playwright HTML report and failure traces
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: memorymedic-playwright-report
          path: |
            e2e/playwright-report/
            e2e/test-results/
          if-no-files-found: warn
          retention-days: 14
```


### `e2e/README.md`

````markdown
# MemoryMedic AI 2.0 — Real-Browser Integration Testing

These tests use Chromium, the actual React frontend, the actual FastAPI backend,
real CSV parsing, and saved sklearn-model inference. Test-only CSVs and a
throwaway sklearn model are generated under `artifacts/e2e/`, which is excluded
from Git by the repository's `.gitignore`.

**Important:** The E2E fixture model is deliberately trained on its own synthetic
fixture data to verify integration, **not ML performance**. It does not
constitute an independent benchmark or held-out accuracy result.

## First-time setup (from repository root)

1. Install Python packages into a dedicated, gitignored E2E virtual environment:

   ```bash
   python3 -m venv artifacts/e2e-venv
   artifacts/e2e-venv/bin/python -m pip install -r ml/requirements.txt -r backend/requirements.txt
   ```

2. Install both Node dependency sets and Playwright Chromium:

   ```bash
   cd frontend && npm ci && cd ..
   cd e2e && npm install --save-dev @playwright/test && npx playwright install chromium && cd ..
   ```

3. From the repository root, run the E2E tests:

   ```bash
   cd e2e
   MEMORYMEDIC_E2E_PYTHON="$(cd .. && pwd)/artifacts/e2e-venv/bin/python" npm test
   ```

4. View successful attachments and failed screenshots / traces:

   ```bash
   npm run report
   ```

### Ports

- Frontend: `http://127.0.0.1:5174`
- Backend: `http://127.0.0.1:8011`

Playwright starts and stops both servers automatically. Stop any processes
already using these ports. Existing development ports `5173` and `8001`
remain unchanged.

### Existing Vitest tests

The original `frontend/src/App.test.jsx` and `frontend/vitest.config.js` do not
change. They remain runnable with:

```bash
cd frontend
npm test
npm run lint
npm run build
```

### CI

The **separate** `.github/workflows/playwright-e2e.yml` GitHub Actions
workflow installs Chromium, executes these browser tests, and uploads the
HTML report and traces. Commit `e2e/package-lock.json` after `npm install`:
CI uses `npm ci` and requires that lockfile.

### Why the isolated configuration is needed

By default, FastAPI reads `data/demo_*` and saved models from `artifacts/ml/`.
The E2E run instead overrides `MEMORYMEDIC_DATA_ROOT` and
`MEMORYMEDIC_MODEL_ROOT`, and Vite's `MEMORYMEDIC_API_ORIGIN` points only to
the E2E backend. Normal application behavior still uses the original defaults.
````


## Changes to existing files made by the patch script

**Only these three existing files change:**

1. `backend/app/metrics.py` imports `os`, then uses
   `DATA_ROOT = Path(os.environ.get("MEMORYMEDIC_DATA_ROOT", str(PROJECT_ROOT / "data")))`.
2. `backend/app/predictions.py` imports `os`, then uses
   `MODEL_ROOT = Path(os.environ.get("MEMORYMEDIC_MODEL_ROOT", str(PROJECT_ROOT / "artifacts" / "ml")))`.
3. `frontend/vite.config.js` defines
   `const backendTarget = process.env.MEMORYMEDIC_API_ORIGIN || 'http://127.0.0.1:8001'`
   and uses `target: backendTarget` in both proxy entries.

No `App.jsx`, `App.test.jsx`, `setupTests.js`, or `vitest.config.js`
changes are necessary.
