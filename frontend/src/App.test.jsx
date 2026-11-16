
import { beforeEach, expect, test, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  LineChart: ({ children }) => (
    <div data-testid="memory-chart">{children}</div>
  ),
  CartesianGrid: () => null,
  Line: () => null,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}))

const samples = [
  {
    timestamp_ms: 1700000000000,
    rss_kb: 40960,
    virtual_memory_kb: 45056,
    peak_rss_kb: 41984,
    threads: 1,
    rss_growth_kb_s: 100,
    minor_faults_s: 2,
    major_faults_s: 0,
    run_id: 'test-run-1',
  },
  {
    timestamp_ms: 1700000001000,
    rss_kb: 45056,
    virtual_memory_kb: 49152,
    peak_rss_kb: 46080,
    threads: 1,
    rss_growth_kb_s: 120,
    minor_faults_s: 3,
    major_faults_s: 0,
    run_id: 'test-run-1',
  },
]

function response(body) {
  return {
    ok: true,
    status: 200,
    json: async () => body,
  }
}

let fetchMock

beforeEach(() => {
  fetchMock = vi.fn(async (url) => {
    if (url === '/health') {
      return response({
        status: 'healthy',
        service: 'memorymedic-api',
      })
    }

    if (url.startsWith('/api/v1/metrics')) {
      const workload = new URL(
        url, 'http://localhost'
      ).searchParams.get('workload')

      return response({
        workload,
        source: 'data/test.csv',
        samples,
      })
    }

    if (url === '/api/v1/predict') {
      return response({
        threshold: 0.5,
        predictions: [
          {
            prediction: 'normal',
            leak_probability: 0.1,
          },
          {
            prediction: 'leak',
            leak_probability: 0.9995,
          },
        ],
      })
    }

    throw new Error(`Unexpected request: ${url}`)
  })

  vi.stubGlobal('fetch', fetchMock)
})

test('loads the dashboard and telemetry', async () => {
  render(<App />)

  expect(
    screen.getByText('Memory intelligence dashboard')
  ).toBeInTheDocument()

  expect(
    await screen.findByText('API connected')
  ).toBeInTheDocument()

  expect(
    screen.getByTestId('memory-chart')
  ).toBeInTheDocument()

  expect(
    screen.getByText('44.0 MB')
  ).toBeInTheDocument()
})

test('switches to linear memory leak', async () => {
  const user = userEvent.setup()
  render(<App />)

  await screen.findByText('API connected')

  await user.selectOptions(
    screen.getByLabelText('Data source'),
    'linear_leak'
  )

  await waitFor(() => {
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/metrics?workload=linear_leak&limit=50',
      expect.any(Object)
    )
  })

  expect(
    screen.getByLabelText('Data source')
  ).toHaveValue('linear_leak')
})

test('runs an AI prediction', async () => {
  const user = userEvent.setup()
  render(<App />)

  const button = await screen.findByRole('button', {
    name: /run ai prediction/i,
  })

  await user.click(button)

  expect(
    await screen.findByText('Potential leak detected')
  ).toBeInTheDocument()

  expect(
    screen.getByText('99.95%')
  ).toBeInTheDocument()

  expect(fetchMock).toHaveBeenCalledWith(
    '/api/v1/predict',
    expect.objectContaining({
      method: 'POST',
    })
  )
})

test('shows a backend error message', async () => {
  fetchMock.mockImplementation(async (url) => {
    if (url === '/health') {
      return response({
        status: 'healthy',
        service: 'memorymedic-api',
      })
    }

    return {
      ok: false,
      status: 503,
      json: async () => ({
        detail: 'Metrics temporarily unavailable',
      }),
    }
  })

  render(<App />)

  const alert = await screen.findByRole('alert')

  expect(alert).toHaveTextContent(
    'Metrics temporarily unavailable'
  )
})

