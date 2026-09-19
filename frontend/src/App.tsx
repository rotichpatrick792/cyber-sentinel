import { useEffect, useState } from 'react';
import { fetchHealth, predict } from './api';
import type { Health, PredictResponse } from './types';

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [featuresText, setFeaturesText] = useState('');
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [predictError, setPredictError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((e) => setHealthError(String(e)));
  }, []);

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

  return (
    <div className="app">
      <header>
        <h1>CyberSentinel</h1>
        <p className="subtitle">AI-powered network threat detection</p>
      </header>

      <main>
        <section className="panel">
          <h2>Backend status</h2>
          {healthError && <p className="error">{healthError}</p>}
          {!healthError && !health && <p>Checking...</p>}
          {health && (
            <p>
              <span className="ok">●</span> {health.status} · {health.environment} ·
              model {health.model_loaded ? 'loaded' : 'not loaded'}
            </p>
          )}
        </section>

        <section className="panel">
          <h2>Manual prediction</h2>
          <p className="hint">
            Paste a JSON object with a <code>features</code> map, then click Predict.
          </p>
          <textarea
            value={featuresText}
            onChange={(e) => setFeaturesText(e.target.value)}
            placeholder='{"features": {"Destination Port": 80, ...}}'
            rows={8}
          />
          <div className="actions">
            <button onClick={handlePredict} disabled={loading || !featuresText.trim()}>
              {loading ? 'Predicting...' : 'Predict'}
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
      </main>
    </div>
  );
}

export default App;
