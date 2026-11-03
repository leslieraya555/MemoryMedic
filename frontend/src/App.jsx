
import { useEffect, useMemo, useState } from 'react'
import {
  Activity, BrainCircuit, CheckCircle2, CircleAlert, Cpu, Database,
  HardDrive, RefreshCw, ShieldCheck, TrendingUp,
} from 'lucide-react'
import {
  CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import './App.css'

const WORKLOADS = [
  { value: 'normal_workload', label: 'Normal workload' },
  { value: 'burst_workload', label: 'Memory burst' },
  { value: 'cache_growth', label: 'Cache growth' },
  { value: 'linear_leak', label: 'Linear memory leak' },
]

async function getJSON(url, options) {
  const response = await fetch(url, options)
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = body?.detail
    const description = Array.isArray(detail)
      ? detail.map((item) => item.msg || JSON.stringify(item)).join('; ')
      : typeof detail === 'string'
        ? detail
        : `HTTP ${response.status}`
    throw new Error(description)
  }

  return body
}

function mb(value) {
  const n = Number(value)
  return value !== null &&
    value !== undefined &&
    value !== '' &&
    Number.isFinite(n)
    ? (n / 1024).toFixed(1)
    : '—'
}

function MetricCard({ icon: Icon, title, value, hint }) {
  return (
    <article className="metric-card">
      <div className="metric-card-top">
        <span>{title}</span>
        <Icon size={18} />
      </div>
      <strong>{value}</strong>
      <small>{hint}</small>
    </article>
  )
}

export default function App() {
  const [workload, setWorkload] = useState('normal_workload')
  const [refresh, setRefresh] = useState(0)
  const [health, setHealth] = useState(null)
  const [telemetry, setTelemetry] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [prediction, setPrediction] = useState(null)
  const [predicting, setPredicting] = useState(false)
  const [predictError, setPredictError] = useState('')

  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()

    setLoading(true)
    setLoadError('')
    setTelemetry(null)
    setPrediction(null)
    setPredictError('')

    async function load() {
      try {
        const [nextHealth, nextTelemetry] = await Promise.all([
          getJSON('/health', { signal: controller.signal }),
          getJSON(
            `/api/v1/metrics?workload=${encodeURIComponent(workload)}&limit=50`,
            { signal: controller.signal },
          ),
        ])

        if (!cancelled) {
          setHealth(nextHealth)
          setTelemetry(nextTelemetry)
        }
      } catch (error) {
        if (!cancelled) {
          setHealth(null)
          setLoadError(
            error instanceof Error ? error.message : String(error),
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()

    return () => {
      cancelled = true
      controller.abort()
    }
  }, [workload, refresh])

  const rows = telemetry?.samples ?? []
  const latest = rows.at(-1)

  const chartData = useMemo(() => rows.map((row, index) => ({
    sample: index + 1,
    rss: Number(row.rss_kb) / 1024,
    virtual: Number(row.virtual_memory_kb) / 1024,
  })), [rows])

  const predRows = prediction?.predictions ?? []
  const leaks = predRows.filter(
    (row) => row.prediction === 'leak',
  ).length
  const latestPrediction = predRows.at(-1)
  const statusHealthy = health?.status === 'healthy'

  async function runPrediction() {
    if (!rows.length) return

    setPredicting(true)
    setPredictError('')
    setPrediction(null)

    try {
      const samples = rows.map((row) => ({
        timestamp_ms: Number(row.timestamp_ms),
        rss_kb: Number(row.rss_kb),
        virtual_memory_kb: Number(row.virtual_memory_kb),
        peak_rss_kb: Number(row.peak_rss_kb),
        threads: Number(row.threads),
        rss_growth_kb_s: Number(row.rss_growth_kb_s),
        minor_faults_s: Number(row.minor_faults_s),
        major_faults_s: Number(row.major_faults_s),
        run_id: row.run_id,
      }))

      if (samples.some((item) =>
        !Number.isInteger(item.timestamp_ms) ||
        !Number.isInteger(item.rss_kb) ||
        item.rss_kb <= 0 ||
        !Number.isInteger(item.virtual_memory_kb) ||
        item.virtual_memory_kb <= 0 ||
        !Number.isInteger(item.peak_rss_kb) ||
        item.peak_rss_kb <= 0 ||
        !Number.isInteger(item.threads) ||
        item.threads <= 0 ||
        typeof item.run_id !== 'string' ||
        !item.run_id.trim() ||
        ![
          item.rss_growth_kb_s,
          item.minor_faults_s,
          item.major_faults_s,
        ].every(Number.isFinite)
      )) {
        throw new Error(
          'Some telemetry values are missing or invalid. Please select another collected demo.',
        )
      }

      const result = await getJSON('/api/v1/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ samples }),
      })

      setPrediction(result)
    } catch (error) {
      setPredictError(
        error instanceof Error ? error.message : String(error),
      )
    } finally {
      setPredicting(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">
            <BrainCircuit size={23} />
          </span>
          <div>
            <strong>MemoryMedic <span>AI</span></strong>
            <small>Process intelligence platform</small>
          </div>
        </div>

        <div className="top-status">
          <span className={`status-dot ${statusHealthy ? 'good' : ''}`} />
          {statusHealthy
            ? 'API connected'
            : loading
              ? 'Connecting…'
              : 'API unavailable'}
        </div>
      </header>

      <main className="content">
        <div className="heading-row">
          <div>
            <div className="eyebrow">MONITORING OVERVIEW</div>
            <h1>Memory intelligence dashboard</h1>
            <p>
              Explore collected Linux process telemetry and run
              your trained memory-leak classifier.
            </p>
          </div>

          <button
            className="refresh-button"
            type="button"
            disabled={loading}
            onClick={() => setRefresh((n) => n + 1)}
          >
            <RefreshCw
              size={16}
              className={loading ? 'spin' : ''}
            />
            Refresh data
          </button>
        </div>

        <section className="toolbar">
          <label htmlFor="workload">Data source</label>
          <select
            id="workload"
            value={workload}
            onChange={(event) => setWorkload(event.target.value)}
          >
            {WORKLOADS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <span className="toolbar-note">
            Historical CSV samples — not live process monitoring
          </span>
        </section>

        {loadError && (
          <div className="error-box" role="alert">
            <CircleAlert size={19} />
            <span>
              Could not load backend data: {loadError}.
              Make sure FastAPI is running on port 8001.
            </span>
          </div>
        )}

        <section
          className="metrics-grid"
          aria-label="Memory measurements"
        >
          <MetricCard
            icon={Activity}
            title="Resident memory (RSS)"
            value={latest ? `${mb(latest.rss_kb)} MB` : '—'}
            hint="Most recent selected sample"
          />
          <MetricCard
            icon={HardDrive}
            title="Virtual memory"
            value={latest ? `${mb(latest.virtual_memory_kb)} MB` : '—'}
            hint="Virtual memory size"
          />
          <MetricCard
            icon={TrendingUp}
            title="Peak resident memory"
            value={latest ? `${mb(latest.peak_rss_kb)} MB` : '—'}
            hint="Peak RSS recorded in sample"
          />
          <MetricCard
            icon={Database}
            title="Samples loaded"
            value={telemetry ? String(rows.length) : '—'}
            hint="Up to 50 recent observations"
          />
        </section>

        <div className="dashboard-grid">
          <section className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <h2>Memory usage over samples</h2>
                <p>
                  RSS and virtual memory, measured in MiB
                </p>
              </div>
              <Activity size={19} />
            </div>

            <div className="chart-wrap">
              {chartData.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chartData}
                    margin={{
                      top: 12,
                      right: 16,
                      left: 2,
                      bottom: 0,
                    }}
                  >
                    <CartesianGrid
                      stroke="#e8eef5"
                      strokeDasharray="4 4"
                    />
                    <XAxis
                      dataKey="sample"
                      tick={{ fontSize: 12 }}
                      stroke="#93a1b5"
                    />
                    <YAxis
                      tick={{ fontSize: 12 }}
                      stroke="#93a1b5"
                      domain={['auto', 'auto']}
                      unit=" MiB"
                      width={76}
                    />
                    <Tooltip
                      formatter={(value) =>
                        `${Number(value).toFixed(2)} MiB`
                      }
                      labelFormatter={(value) => `Sample ${value}`}
                    />
                    <Line
                      dataKey="rss"
                      name="Resident memory"
                      type="monotone"
                      stroke="#5969eb"
                      strokeWidth={2.5}
                      dot={false}
                      isAnimationActive={false}
                    />
                    <Line
                      dataKey="virtual"
                      name="Virtual memory"
                      type="monotone"
                      stroke="#19a89b"
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty">
                  {loading
                    ? 'Loading measurements…'
                    : 'No measurements available'}
                </div>
              )}
            </div>

            <div className="legend">
              <span>
                <i className="legend-rss" /> RSS memory
              </span>
              <span>
                <i className="legend-virtual" /> Virtual memory
              </span>
            </div>
          </section>

          <section className="panel prediction-panel">
            <div className="panel-heading">
              <div>
                <h2>AI memory-leak analysis</h2>
                <p>Predictions from your saved ML model</p>
              </div>
              <BrainCircuit size={19} />
            </div>

            <div className="prediction-content">
              <div className="model-icon">
                <Cpu size={30} />
              </div>

              <h3>
                {latestPrediction
                  ? latestPrediction.prediction === 'leak'
                    ? 'Potential leak detected'
                    : 'Latest sample classified normal'
                  : 'Ready to analyze telemetry'}
              </h3>

              <p>
                {latestPrediction
                  ? `The model classified ${predRows.length} samples; ${leaks} were flagged as leaks.`
                  : 'Run your existing trained model against the selected telemetry samples.'}
              </p>

              {latestPrediction && (
                <div className="prediction-stats">
                  <div>
                    <small>Latest leak probability</small>
                    <strong>
                      {(
                        Number(latestPrediction.leak_probability) * 100
                      ).toFixed(2)}%
                    </strong>
                  </div>
                  <div>
                    <small>Model threshold</small>
                    <strong>
                      {(Number(prediction.threshold) * 100).toFixed(0)}%
                    </strong>
                  </div>
                </div>
              )}

              {predictError && (
                <div className="prediction-error" role="alert">
                  {predictError}
                </div>
              )}

              <button
                type="button"
                className="primary-button"
                onClick={runPrediction}
                disabled={!rows.length || predicting || loading}
              >
                <BrainCircuit size={17} />
                {predicting
                  ? 'Running model…'
                  : 'Run AI prediction'}
              </button>
            </div>
          </section>
        </div>

        <div className="bottom-grid">
          <section className="panel table-panel">
            <div className="panel-heading">
              <div>
                <h2>Recent telemetry</h2>
                <p>
                  Latest measurements from the selected workload
                </p>
              </div>
              <Database size={19} />
            </div>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Sample</th>
                    <th>RSS (MiB)</th>
                    <th>Virtual (MiB)</th>
                    <th>Threads</th>
                    <th>Growth (KiB/s)</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.slice(-8).reverse().map((row, index) => (
                    <tr key={`${row.timestamp_ms}-${index}`}>
                      <td>{rows.length - index}</td>
                      <td>{mb(row.rss_kb)}</td>
                      <td>{mb(row.virtual_memory_kb)}</td>
                      <td>{row.threads}</td>
                      <td>
                        {Number(row.rss_growth_kb_s).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                  {!rows.length && (
                    <tr>
                      <td colSpan={5}>No telemetry loaded</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel info-panel">
            <div className="panel-heading">
              <div>
                <h2>Data and system</h2>
                <p>Current backend response details</p>
              </div>
              <ShieldCheck size={19} />
            </div>

            <div className="detail-row">
              <span>API service</span>
              <b>{health?.service ?? 'Unavailable'}</b>
            </div>

            <div className="detail-row">
              <span>API status</span>
              <b>{health?.status ?? 'Unknown'}</b>
            </div>

            <div className="detail-row">
              <span>Workload</span>
              <b>{telemetry?.workload ?? '—'}</b>
            </div>

            <div className="detail-row">
              <span>Source file</span>
              <code title={telemetry?.source ?? ''}>
                {telemetry?.source ?? '—'}
              </code>
            </div>

            <div className="data-note">
              <CheckCircle2 size={16} />
              Read-only CSV monitoring. Predictions are requested
              only when you press the AI button.
            </div>
          </section>
        </div>

        <footer>
          MemoryMedic AI 2.0 · Linux process telemetry · FastAPI + React
        </footer>
      </main>
    </div>
  )
}
