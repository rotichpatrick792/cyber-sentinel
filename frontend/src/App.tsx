import { useEffect, useState } from 'react';

type Health = {
  status: string;
  environment: string;
  model_loaded: boolean;
  model_error: string | null;
};

const API_BASE = 'http://127.0.0.1:8000';

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="app">
      <header>
        <h1>CyberSentinel</h1>
        <p className="subtitle">AI-powered network threat detection</p>
      </header>

      <main>
        <h2>Backend status</h2>
        {error && <p className="error">Cannot reach backend: {error}</p>}
        {!error && !health && <p>Checking...</p>}
        {health && (
          <ul>
            <li>Status: <strong>{health.status}</strong></li>
            <li>Environment: {health.environment}</li>
            <li>
              Model loaded:{' '}
              <strong className={health.model_loaded ? 'ok' : 'bad'}>
                {health.model_loaded ? 'yes' : 'no'}
              </strong>
            </li>
            {health.model_error && <li className="error">Error: {health.model_error}</li>}
          </ul>
        )}
      </main>
    </div>
  );
}

export default App;
