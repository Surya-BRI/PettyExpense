import { useState, type FormEvent } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../auth/context';
import { Icon } from '../components/Icon';
import { usePageTitle } from '../lib/usePageTitle';

// Same region choices as the mobile login; the backend rejects a region a
// multi-region user isn't assigned to.
const REGIONS = [
  { code: 'UAE', label: 'UAE' },
  { code: 'KSA', label: 'KSA' },
  { code: 'OMAN', label: 'Oman' },
];
const REGION_KEY = 'pe_last_region';
const YEAR = new Date().getFullYear();

function lastRegion(): string {
  try {
    const saved = localStorage.getItem(REGION_KEY);
    return REGIONS.some((r) => r.code === saved) ? saved! : 'UAE';
  } catch {
    return 'UAE';
  }
}

export function LoginPage() {
  usePageTitle('Sign in');
  const { user, login, sessionExpired } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [region, setRegion] = useState(lastRegion);
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(undefined);
    try {
      await login(username.trim(), password, region);
      try {
        localStorage.setItem(REGION_KEY, region);
      } catch {
        /* remembering the region is a convenience only */
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login">
      <div className="login-art">
        <div className="row" style={{ gap: 12, position: 'relative', zIndex: 1 }}>
          <img src="/brand/logo_br_mark.png" alt="" width={44} height={44} />
          <div>
            <div className="strong" style={{ fontSize: 16 }}>Blue Rhine Industries</div>
            <div style={{ fontSize: 12, opacity: 0.65 }}>Petty Cash &amp; Expense Tracker</div>
          </div>
        </div>
        <div className="big" style={{ position: 'relative', zIndex: 1 }}>
          Every claim, every approval, <span>one view.</span>
        </div>
        <p style={{ position: 'relative', zIndex: 1 }}>
          Follow what employees submit from the mobile app, see exactly where each bill is waiting, and track what has been paid out.
        </p>
        <ul style={{ position: 'relative', zIndex: 1 }}>
          <li>Live totals by region, category and employee</li>
          <li>HOD, Accountant and Finance Manager approvals</li>
          <li>Duplicate and unmatched-vendor checks</li>
        </ul>
        <div className="foot">© {YEAR} Blue Rhine Industries · Internal use only</div>
      </div>

      <div className="login-form">
        <form className="login-box" onSubmit={submit} noValidate>
          <img src="/brand/Br_fulllogo.png" alt="Blue Rhine Industries" style={{ width: 210, marginBottom: 4 }} />
          <div>
            <h2>Sign in</h2>
            <p className="muted" style={{ marginTop: 4 }}>Use the same account as the mobile app.</p>
          </div>

          {sessionExpired && !error && (
            <div className="notice">Your session expired. Please sign in again.</div>
          )}

          <div className="field">
            <span id="region-label">Region</span>
            <div className="seg" role="radiogroup" aria-labelledby="region-label">
              {REGIONS.map((r) => (
                <button
                  type="button"
                  key={r.code}
                  role="radio"
                  aria-checked={region === r.code}
                  className={region === r.code ? 'on' : undefined}
                  onClick={() => setRegion(r.code)}
                  style={{ flex: 1 }}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>

          <label className="field">
            Username
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              autoFocus
              required
            />
          </label>

          <label className="field">
            Password
            <span className="input-wrap">
              <input
                className="input"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                style={{ paddingRight: 44 }}
              />
              <button
                type="button"
                className="btn btn-ghost btn-sm trail"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                <Icon name={showPassword ? 'eyeOff' : 'eye'} size={18} />
              </button>
            </span>
          </label>

          {error && (
            <div className="error-box" role="alert">
              <span>{error}</span>
            </div>
          )}

          <button className="btn btn-primary btn-lg" type="submit" disabled={busy || !username.trim() || !password}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
          <p className="muted small" style={{ textAlign: 'center' }}>
            Trouble signing in? Contact your administrator.
          </p>
        </form>
      </div>
    </div>
  );
}
