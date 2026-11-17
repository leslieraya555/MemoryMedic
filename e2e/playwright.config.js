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
