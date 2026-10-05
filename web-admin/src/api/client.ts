import type {
  ActivityItem,
  AppNotification,
  AuthUser,
  Claim,
  Stage,
  TokenResponse,
  VendorRef,
} from './types';

/** Backend base URL -- set VITE_API_BASE_URL in web-admin/.env. Falls back to production. */
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'https://expensetracker-api.app-brisigns.com').replace(
  /\/+$/,
  '',
);

const ACCESS_KEY = 'pe_access_token';
const REFRESH_KEY = 'pe_refresh_token';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const tokens = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(access: string, refresh: string) {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

/** Called when the session is gone for good (refresh token rejected) -- AuthProvider logs out. */
let onSessionExpired: () => void = () => {};
export function setSessionExpiredHandler(fn: () => void) {
  onSessionExpired = fn;
}

async function parseError(res: Response): Promise<ApiError> {
  let message = `Request failed (${res.status})`;
  try {
    const body = await res.json();
    if (body?.detail) message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
  } catch {
    /* non-JSON error body */
  }
  return new ApiError(res.status, message);
}

// One in-flight refresh shared by every request that hits a 401 at the same time.
let refreshing: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  const refresh = tokens.refresh;
  if (!refresh) return false;
  refreshing ??= (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) return false;
      const data = (await res.json()) as TokenResponse;
      tokens.set(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

/** Authenticated fetch: adds the bearer token, and on a 401 refreshes once and retries. */
async function authFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const run = () =>
    fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...(tokens.access ? { Authorization: `Bearer ${tokens.access}` } : {}),
        ...init.headers,
      },
    });
  let res = await run();
  if (res.status === 401) {
    if (await refreshSession()) {
      res = await run();
    } else {
      tokens.clear();
      onSessionExpired();
    }
  }
  return res;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await authFetch(path, init);
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  async login(username: string, password: string, regionCode: string): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, region_code: regionCode }),
    });
    if (!res.ok) throw await parseError(res);
    return (await res.json()) as TokenResponse;
  },

  me: () => request<AuthUser>('/api/auth/me'),

  /** Whole company -- hod / accountant / finance_manager / admin only. */
  allClaims: () => request<Claim[]>('/api/admin/claims'),
  myClaims: () => request<Claim[]>('/api/claims/mine'),

  /** Approver view of one claim (includes history + live duplicate check). */
  approvalClaim: (id: number) => request<Claim>(`/api/approvals/${id}`),
  /** Employee view of their own claim. */
  myClaim: (id: number) => request<Claim>(`/api/claims/${id}`),

  queue: (stage: Stage) => request<Claim[]>(`/api/approvals/queue?stage=${stage}`),
  approve: (id: number, comment?: string) => post<Claim>(`/api/approvals/${id}/approve`, { comment: comment || null }),
  dispute: (id: number, comment: string) => post<Claim>(`/api/approvals/${id}/dispute`, { comment }),
  reject: (id: number, comment: string) => post<Claim>(`/api/approvals/${id}/reject`, { comment }),
  markPaid: (id: number, remarks?: string) => post<Claim>(`/api/admin/claims/${id}/mark-paid`, { remarks: remarks || null }),
  resolveVendor: (id: number, body: { vendor_id?: number; create_new?: boolean }) =>
    post<Claim>(`/api/approvals/${id}/resolve-vendor`, { vendor_id: body.vendor_id ?? null, create_new: !!body.create_new }),
  vendors: () => request<VendorRef[]>('/api/vendors'),

  submitDraft: (id: number) => post<Claim>(`/api/claims/${id}/submit`),
  resubmit: (id: number) => post<Claim>(`/api/claims/${id}/resubmit`),

  /** Company-wide workflow feed. Returns null when the backend doesn't have the endpoint yet. */
  async activity(limit = 40): Promise<ActivityItem[] | null> {
    const res = await authFetch(`/api/admin/activity?limit=${limit}`);
    if (res.status === 404) return null;
    if (!res.ok) throw await parseError(res);
    return (await res.json()) as ActivityItem[];
  },

  notifications: (limit = 50) => request<AppNotification[]>(`/api/notifications?limit=${limit}`),
  unreadCount: () => request<{ unread: number }>('/api/notifications/unread-count').then((r) => r.unread),
  markRead: (id: number) => post<{ ok: boolean }>(`/api/notifications/${id}/read`),
  markAllRead: () => post<{ marked: number }>('/api/notifications/read-all'),

  /**
   * Receipt image as an object URL. A presigned S3 URL is already authorized (adding our
   * bearer token would make S3 reject it); the backend proxy path needs the token.
   */
  async receiptImage(url: string): Promise<string> {
    if (/^https?:\/\//.test(url)) return url;
    const res = await authFetch(url);
    if (!res.ok) throw await parseError(res);
    return URL.createObjectURL(await res.blob());
  },
};
