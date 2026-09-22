import { useEffect, useMemo, useState } from 'react';
import { fetchHealth, fetchRecentFlows, predict } from './api';
import { clearToken, getToken } from './auth';
import Login from './Login';
import type { FlowRecord, Health, PredictResponse } from './types';

const POLL_MS = 2000;

function App() {
  const [token, setTokenState] = useState<string | null>(() => getToken());

  if (!token) {
    return <Login onSuccess={() => setTokenState(getToken())} />;
  }

  return <Dashboard onLogout={() => {
    clearToken();
    setTokenState(null);
  }} />;
}

function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [flows, setFlows] = useState<FlowRecord[]>([]);

  const [featuresText, setFeaturesText] = useState('');
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [predictError, setPredictError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((e) => setHealthError(String(e)));
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function tick() {
      try {
        const data = await fetchRecentFlows(200);
        if (!cancelled) setFlows(data.flows);
      } catch {
        /* ignore */
      }
    }
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const alerts = useMemo(() => flows.filter((f) => f.label !== 'BENIGN'), [flows]);
  const benignCount = flows.length - alerts.length;

  async function handlePredict() {
    setLoading(true);
    setPredictError(null);
    setResult(null);
    try {
      const parsed = JSON.parse(featuresText);
      const features = parsed.features ?? parsed;
      const res = await predict(features);
      setResult(res);
    } catch (e) {
      setPredictError(String(e));
    } finally {
      setLoading(false);
    }
  }

  const modelStatus = health?.model_loaded ? 'online' : healthError ? 'down' : '…';

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>CyberSentinel</h1>
          <p className="subtitle">AI-powered network threat detection</p>
        </div>
        <div className="topbar-right">
          <div className={`status-pill ${modelStatus}`}>
            <span className="dot" /> model {modelStatus}
          </div>
          <button className="logout-btn" onClick={onLogout}>
            Log out
          </button>
        </div>
      </header>

      <section className="stats-row">
        <Stat label="recent flows" value={flows.length} />
        <Stat label="benign" value={benignCount} tone="ok" />
        <Stat label="alerts" value={alerts.length} tone={alerts.length > 0 ? 'bad' : undefined} />
        <Stat label="model" value={modelStatus} />
      </section>

      <main className="grid">
        <section className="panel">
          <h2>Live feed</h2>
          {flows.length === 0 ? (
            <p className="hint">
              No flows yet. Run <code>python network-monitor/detect.py</code> to start
              monitoring.
            </p>
          ) : (
            <div className="table-wrap">
              <table className="flows">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Source</th>
                    <th>Destination</th>
                    <th>Label</th>
                    <th>Conf.</th>
                  </tr>
                </thead>
                <tbody>
                  {flows.map((f, i) => (
                    <tr key={i} className={f.label !== 'BENIGN' ? 'alert-row' : ''}>
                      <td className="mono">
                        {f.timestamp ? f.timestamp.slice(11, 19) : '—'}
                      </td>
                      <td className="mono">
                        {f.src_ip}:{f.src_port}
                      </td>
                      <td className="mono">
                        {f.dst_ip}:{f.dst_port}
                      </td>
                      <td>
                        <span className={f.label === 'BENIGN' ? 'ok' : 'bad'}>
                          {f.label}
                        </span>
                      </td>
                      <td className="mono">{(f.confidence * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <div className="side-col">
          <section className="panel">
            <h2>
              Alerts{' '}
              <span className={alerts.length > 0 ? 'badge bad' : 'badge'}>
                {alerts.length}
              </span>
            </h2>
            {alerts.length === 0 ? (
              <p className="hint">
                <span className="ok">●</span> No threats detected.
              </p>
            ) : (
              <ul className="alerts-list">
                {alerts.slice(0, 10).map((f, i) => (
                  <li key={i} className="alert-item">
                    <div className="alert-label bad">{f.label}</div>
                    <div className="alert-detail mono">
                      {f.src_ip}:{f.src_port} → {f.dst_ip}:{f.dst_port}
                    </div>
                    <div className="alert-meta">
                      {(f.confidence * 100).toFixed(1)}% ·{' '}
                      {f.timestamp ? f.timestamp.slice(11, 19) : '—'}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="panel">
            <h2>Manual prediction</h2>
            <p className="hint">
              Paste a JSON object with a <code>features</code> map.
            </p>
            <textarea
              value={featuresText}
              onChange={(e) => setFeaturesText(e.target.value)}
              placeholder='{"features": {"Destination Port": 80, ...}}'
              rows={5}
            />
            <div className="actions">
              <button onClick={handlePredict} disabled={loading || !featuresText.trim()}>
                {loading ? 'Predicting…' : 'Predict'}
              </button>
            </div>

            {predictError && <p className="error">{predictError}</p>}

            {result && (
              <div className="result">
                <p className="label-big">{result.label}</p>
                <p className="confidence">
                  confidence: {(result.confidence * 100).toFixed(1)}%
                </p>
                <ul className="probs">
                  {Object.entries(result.probabilities)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([name, p]) => (
                      <li key={name}>
                        <span className="prob-name">{name}</span>
                        <span className="prob-bar">
                          <span
                            className="prob-fill"
                            style={{ width: `${(p * 100).toFixed(2)}%` }}
                          />
                        </span>
                        <span className="prob-value">{(p * 100).toFixed(1)}%</span>
                      </li>
                    ))}
                </ul>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: 'ok' | 'bad';
}) {
  return (
    <div className="stat">
      <div className={`stat-value ${tone ?? ''}`}>{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export default App;
