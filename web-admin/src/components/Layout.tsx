import { useEffect, useState, type ReactNode } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { API_BASE, api } from '../api/client';
import { useAuth, useUser } from '../auth/context';
import { ROLE_LABELS, isApprover, stagesFor } from '../lib/format';
import { usePageTitle } from '../lib/usePageTitle';
import { Icon, type IconName } from './Icon';

const POLL_MS = 60_000;

/** Unread alerts + claims waiting on this approver, refreshed every minute for the sidebar badges. */
function useBadgeCounts() {
  const user = useUser();
  const [unread, setUnread] = useState(0);
  const [waiting, setWaiting] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const n = await api.unreadCount();
        if (!cancelled) setUnread(n);
      } catch {
        /* badge is best-effort */
      }
      const stages = stagesFor(user.role);
      if (stages.length === 0) return;
      try {
        const queues = await Promise.all(stages.map((s) => api.queue(s)));
        if (!cancelled) setWaiting(queues.reduce((sum, q) => sum + q.length, 0));
      } catch {
        /* badge is best-effort */
      }
    };
    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [user.role]);

  return { unread, waiting };
}

function NavItem({ to, icon, label, count, end }: { to: string; icon: IconName; label: string; count?: number; end?: boolean }) {
  return (
    <NavLink to={to} end={end} className={({ isActive }) => (isActive ? 'active' : undefined)} title={label}>
      <Icon name={icon} />
      <span className="lbl">{label}</span>
      {!!count && <span className="count">{count > 99 ? '99+' : count}</span>}
    </NavLink>
  );
}

export function Layout() {
  const user = useUser();
  const { logout } = useAuth();
  const { unread, waiting } = useBadgeCounts();
  const approver = isApprover(user);

  return (
    <div className="frame">
      <aside className="sidebar" aria-label="Main navigation">
        <div className="brand">
          <img src="/brand/logo_br_mark.png" alt="Blue Rhine" />
          <div className="brand-text">
            <div className="brand-name">Expense Tracker</div>
            <div className="brand-sub">Blue Rhine Industries</div>
          </div>
        </div>
        <nav className="nav">
          <div className="nav-section">Overview</div>
          <NavItem to="/" end icon="dashboard" label="Dashboard" />
          <NavItem to="/claims" icon="claims" label={approver ? 'All claims' : 'My claims'} />
          {approver && <NavItem to="/approvals" icon="queue" label="Approvals" count={waiting} />}
          <div className="nav-section">Account</div>
          <NavItem to="/notifications" icon="bell" label="Notifications" count={unread} />
          <NavItem to="/profile" icon="person" label="Profile" />
        </nav>
        <div className="sidebar-foot">
          <Link to="/profile" className="who-link" title="Open your profile">
            <div className="avatar">{(user.display_name || '?').trim().charAt(0).toUpperCase()}</div>
            <div className="who">
              <div className="name">{user.display_name}</div>
              <div className="meta">
                {ROLE_LABELS[user.role] ?? user.role}
                {user.region_code ? ` · ${user.region_code}` : ''}
              </div>
            </div>
          </Link>
          <button className="icon-btn" onClick={logout} title="Sign out" aria-label="Sign out">
            <Icon name="logout" />
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

const envLabel = API_BASE.includes('127.0.0.1') || API_BASE.includes('localhost') ? 'Local backend' : null;

/** Sticky page header: title, optional breadcrumb line, and page actions on the right. */
/**
 * Sticky page header. Its content sits in the same centered container as the page body
 * (`narrow` must match the page's `.page.narrow`), so the title lines up with the cards below.
 */
export function Topbar({
  title,
  crumbs,
  narrow,
  children,
}: {
  title: string;
  crumbs?: ReactNode;
  narrow?: boolean;
  children?: ReactNode;
}) {
  usePageTitle(title);
  return (
    <header className="topbar">
      <div className={`topbar-inner${narrow ? ' narrow' : ''}`}>
        <div style={{ minWidth: 0 }}>
          {crumbs && <div className="crumbs">{crumbs}</div>}
          <h1>{title}</h1>
        </div>
        <div className="spacer" />
        {envLabel && <span className="env-pill" title={API_BASE}>{envLabel}</span>}
        {children && <div className="topbar-actions">{children}</div>}
      </div>
    </header>
  );
}
