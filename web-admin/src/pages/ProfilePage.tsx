import { Link } from 'react-router-dom';
import { API_BASE, api } from '../api/client';
import { useAuth, useUser } from '../auth/context';
import { Icon } from '../components/Icon';
import { Topbar } from '../components/Layout';
import { Card, EmptyState, Skel } from '../components/ui';
import { PENDING, ROLE_LABELS, STAGE_LABELS, isApprover, plural, stagesFor } from '../lib/format';
import { useAsync } from '../lib/useAsync';

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return 'U';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

export function ProfilePage() {
  const user = useUser();
  const { logout } = useAuth();
  const approver = isApprover(user);

  return (
    <>
      <Topbar narrow title="Profile" crumbs="Account" />
      <div className="page narrow stack">
        <section className="card profile-hero">
          <div className="profile-avatar">{initials(user.display_name || user.username || 'U')}</div>
          <div style={{ minWidth: 0 }}>
            <h2 style={{ fontSize: 22 }}>{user.display_name}</h2>
            <div className="row" style={{ marginTop: 8 }}>
              <span className="tag">{ROLE_LABELS[user.role] ?? user.role}</span>
              {user.region_code && <span className="tag">Signed in: {user.region_code}</span>}
              {user.department_name && <span className="tag">{user.department_name}</span>}
            </div>
          </div>
          <button className="btn btn-danger profile-signout" onClick={logout}>
            <Icon name="logout" size={16} /> Sign out
          </button>
        </section>

        <div className={approver ? 'grid-2' : 'stack'}>
          <Card title="Account details">
            <dl className="kv">
              <dt>Name</dt>
              <dd>{user.display_name}</dd>
              <dt>Username</dt>
              <dd>{user.username ?? '-'}</dd>
              <dt>Email</dt>
              <dd>{user.email || '-'}</dd>
              <dt>Role</dt>
              <dd>{ROLE_LABELS[user.role] ?? user.role}</dd>
              <dt>Department</dt>
              <dd>{user.department_name ?? (user.department_id ? `#${user.department_id}` : '-')}</dd>
              <dt>Region</dt>
              <dd>{user.region_code ?? '-'}</dd>
              <dt>User ID</dt>
              <dd className="num">{user.id}</dd>
            </dl>
          </Card>
          {approver && <ApproverSummary />}
        </div>

        <Card title="Session">
          <dl className="kv">
            <dt>Connected to</dt>
            <dd style={{ wordBreak: 'break-all' }}>{API_BASE}</dd>
            <dt>Region</dt>
            <dd>{user.region_code ?? 'Not selected'} · sign out to switch region</dd>
          </dl>
          <p className="muted small" style={{ margin: '14px 0 0' }}>
            Name, email, role and department are managed by the admin — contact them if something here is wrong.
          </p>
        </Card>
      </div>
    </>
  );
}

/** Approver: what is waiting on them right now, per stage they cover. */
function ApproverSummary() {
  const user = useUser();
  const stages = stagesFor(user.role);
  const queues = useAsync(() => Promise.all(stages.map((s) => api.queue(s))), [user.role]);
  const total = (queues.data ?? []).reduce((n, q) => n + q.length, 0);
  return (
    <Card title="Waiting for you" right={<Link className="btn btn-sm" to="/approvals">Open approvals</Link>}>
      {queues.loading && !queues.data ? (
        <div className="stack"><Skel w="30%" h={22} /><Skel w="70%" h={12} /></div>
      ) : queues.error ? (
        <EmptyState title="Couldn’t load your queue">{queues.error.message}</EmptyState>
      ) : (
        <div className="stack" style={{ gap: 12 }}>
          <div className="strong" style={{ fontSize: 20 }}>{plural(total, 'claim')}</div>
          <dl className="kv">
            {stages.map((s, i) => {
              const q = queues.data?.[i] ?? [];
              const disputed = q.filter((c) => c.status === 'disputed').length;
              const open = q.filter((c) => PENDING.includes(c.status)).length;
              return [
                <dt key={`${s}-t`}>{STAGE_LABELS[s]}</dt>,
                <dd key={`${s}-d`}>
                  {plural(open, 'claim')}
                  {disputed ? <span className="muted"> · {disputed} with employee</span> : null}
                </dd>,
              ];
            })}
          </dl>
        </div>
      )}
    </Card>
  );
}
