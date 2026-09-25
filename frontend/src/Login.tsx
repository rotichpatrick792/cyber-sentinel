import { useState } from 'react';
import { login, register } from './api';
import { setToken } from './auth';

type Mode = 'login' | 'register';

function Login({ onSuccess }: { onSuccess: () => void }) {
    const [mode, setMode] = useState<Mode>('login');
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            if (mode === 'register') {
                await register(username, email, password);
                // Auto-login after successful registration.
            }
            const token = await login(username, password);
            setToken(token);
            onSuccess();
        } catch (err) {
            setError(String(err));
        } finally {
            setLoading(false);
        }
    }

    function switchMode() {
        setMode(mode === 'login' ? 'register' : 'login');
        setError(null);
    }

    return (
        <div className="login-page">
            <form className="login-card" onSubmit={handleSubmit}>
                <h1>CyberSentinel</h1>
                <p className="subtitle">
                    {mode === 'login' ? 'Sign in to continue' : 'Create an account'}
                </p>

                <label>
                    <span>Username</span>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        autoComplete="username"
                        minLength={3}
                        required
                    />
                </label>

                {mode === 'register' && (
                    <label>
                        <span>Email</span>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            autoComplete="email"
                            required
                        />
                    </label>
                )}

                <label>
                    <span>Password</span>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                        minLength={8}
                        required
                    />
                </label>

                {error && <p className="error">{error}</p>}

                <button type="submit" disabled={loading}>
                    {loading
                        ? mode === 'login'
                            ? 'Signing in…'
                            : 'Creating account…'
                        : mode === 'login'
                            ? 'Sign in'
                            : 'Create account'}
                </button>

                <button
                    type="button"
                    className="link-btn"
                    onClick={switchMode}
                    disabled={loading}
                >
                    {mode === 'login'
                        ? "Don't have an account? Register"
                        : 'Already have an account? Sign in'}
                </button>
            </form>
        </div>
    );
}

export default Login;
