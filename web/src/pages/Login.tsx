import { useState, useEffect } from 'react';
import { login, register, loginWithPasskey, getPasskeyStatus } from '../auth';

interface LoginProps {
  onLogin: () => void;
}

type AuthMode = 'login' | 'register';

export default function Login({ onLogin }: LoginProps) {
  const [mode, setMode] = useState<AuthMode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasPasskey, setHasPasskey] = useState(false);
  const [checkingPasskey, setCheckingPasskey] = useState(true);

  useEffect(() => {
    // Only check passkey status for login mode (requires no auth for the begin endpoint)
    getPasskeyStatus()
      .then((s) => setHasPasskey(s.registered))
      .catch(() => {})
      .finally(() => setCheckingPasskey(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'register') {
        await register(username, password, displayName || undefined);
      } else {
        await login(username, password);
      }
      onLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePasskey = async () => {
    setError('');
    setLoading(true);
    try {
      await loginWithPasskey();
      onLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Biometric auth failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <span className="login-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </span>
          <h1>MindPalace</h1>
          <p>{mode === 'login' ? 'Sign in to access your data' : 'Create your account'}</p>
        </div>

        {mode === 'login' && !checkingPasskey && hasPasskey && (
          <div className="passkey-section">
            <button className="passkey-btn" onClick={handlePasskey} disabled={loading}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <circle cx="12" cy="16" r="1" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              Sign in with Biometrics
            </button>
            <div className="login-divider">
              <span>or use password</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          {mode === 'register' && (
            <div className="form-group">
              <input
                type="text"
                placeholder="Display name (optional)"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                autoComplete="name"
              />
            </div>
          )}
          <div className="form-group">
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              required
            />
          </div>
          {error && <div className="login-error">{error}</div>}
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? (mode === 'register' ? 'Creating account...' : 'Signing in...') : (mode === 'register' ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div className="auth-switch">
          {mode === 'login' ? (
            <p>Don't have an account? <button className="link-btn" onClick={() => { setMode('register'); setError(''); }}>Register</button></p>
          ) : (
            <p>Already have an account? <button className="link-btn" onClick={() => { setMode('login'); setError(''); }}>Sign in</button></p>
          )}
        </div>
      </div>
    </div>
  );
}
