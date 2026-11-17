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
