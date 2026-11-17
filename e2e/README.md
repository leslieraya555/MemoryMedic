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
