import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api, setSessionExpiredHandler, tokens } from '../api/client';
import type { AuthUser } from '../api/types';
import { AuthContext } from './context';

// `/api/auth/me` omits username; the login response has it, so keep the last known one.
const USER_KEY = 'pe_user';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  // Only a stored token needs checking; without one we know immediately there's no session.
  const [loading, setLoading] = useState(() => !!tokens.access);
  const [sessionExpired, setSessionExpired] = useState(false);

  const logout = useCallback(() => {
    tokens.clear();
    localStorage.removeItem(USER_KEY);
    setUser(null);
  }, []);

  useEffect(() => {
    setSessionExpiredHandler(() => {
      setSessionExpired(true);
      logout();
    });
    if (!tokens.access) return;
    // Validates the stored token (refreshing it if expired) and reloads the user.
    api
      .me()
      .then((me) => {
        const cached = JSON.parse(localStorage.getItem(USER_KEY) || 'null') as AuthUser | null;
        setUser({ ...cached, ...me });
      })
      .catch(logout)
      .finally(() => setLoading(false));
  }, [logout]);

  const login = useCallback(async (username: string, password: string, region: string) => {
    const data = await api.login(username, password, region);
    tokens.set(data.access_token, data.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setSessionExpired(false);
    setUser(data.user);
  }, []);

  const value = useMemo(
    () => ({ user, loading, sessionExpired, login, logout }),
    [user, loading, sessionExpired, login, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
