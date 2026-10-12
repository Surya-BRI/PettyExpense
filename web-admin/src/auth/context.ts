import { createContext, useContext } from 'react';
import type { AuthUser } from '../api/types';

export interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  /** True once when the user was signed out because their session expired (not a manual sign-out). */
  sessionExpired: boolean;
  login: (username: string, password: string, region: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}

/** The signed-in user; only call inside routes guarded by <RequireAuth>. */
export function useUser(): AuthUser {
  const { user } = useAuth();
  if (!user) throw new Error('No signed-in user');
  return user;
}
