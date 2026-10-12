import type { ReactNode } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { useAuth } from './auth/context';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Layout } from './components/Layout';
import { Toaster } from './components/Toaster';
import { isApprover } from './lib/format';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { ClaimDetailPage } from './pages/ClaimDetailPage';
import { ClaimsPage } from './pages/ClaimsPage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { ProfilePage } from './pages/ProfilePage';

/** Branded splash while a stored session is being validated. */
function BootScreen() {
  return (
    <div className="state-page">
      <div style={{ display: 'grid', justifyItems: 'center', gap: 16 }}>
        <img src="/brand/logo_br_mark.png" alt="" width={48} height={48} />
        <div className="spinner" role="status" aria-label="Loading" />
      </div>
    </div>
  );
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <BootScreen />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function ApproverOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return user && isApprover(user) ? <>{children}</> : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <ErrorBoundary>
      <Toaster>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                element={
                  <RequireAuth>
                    <Layout />
                  </RequireAuth>
                }
              >
                <Route index element={<DashboardPage />} />
                <Route path="claims" element={<ClaimsPage />} />
                <Route path="claims/:id" element={<ClaimDetailPage />} />
                <Route path="approvals" element={<ApproverOnly><ApprovalsPage /></ApproverOnly>} />
                <Route path="notifications" element={<NotificationsPage />} />
                <Route path="profile" element={<ProfilePage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </Toaster>
    </ErrorBoundary>
  );
}
