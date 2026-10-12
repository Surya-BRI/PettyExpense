import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { Stage } from '../api/types';
import { useUser } from '../auth/context';
import { Icon } from '../components/Icon';
import { Topbar } from '../components/Layout';
import { EmptyState, ErrorBox, Skel, StatusBadge } from '../components/ui';
import { STAGE_LABELS, claimTotal, formatDate, money, stagesFor, timeAgo, vendorOf } from '../lib/format';
import { useAsync } from '../lib/useAsync';

/** The claims waiting on this approver (backend-filtered to the assigned approver per stage). */
export function ApprovalsPage() {
  const user = useUser();
  const stages = stagesFor(user.role);
  const [stage, setStage] = useState<Stage>(stages[0] ?? 'hod');
  const navigate = useNavigate();
  const queue = useAsync(() => api.queue(stage), [stage]);

  // New submissions first, then disputed ones (those are back with the employee).
  const rows = [...(queue.data ?? [])].sort(
    (a, b) => Number(a.status === 'disputed') - Number(b.status === 'disputed') || b.id - a.id,
  );

  return (
    <>
      <Topbar narrow title="Approvals" crumbs="Waiting for your decision">
        <button className="btn btn-sm" onClick={queue.reload}>
          <Icon name="refresh" size={16} /> Refresh
        </button>
      </Topbar>
      <div className="page narrow stack">
        {stages.length > 1 && (
          <div className="seg" style={{ alignSelf: 'flex-start' }}>
            {stages.map((s) => (
              <button key={s} className={s === stage ? 'on' : undefined} onClick={() => setStage(s)}>
                {STAGE_LABELS[s]}
              </button>
            ))}
          </div>
        )}
        {queue.error && <ErrorBox error={queue.error} onRetry={queue.reload} />}
        {queue.loading && !queue.data ? (
          <div className="card card-pad stack" style={{ gap: 16 }}>
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="row" style={{ flexWrap: 'nowrap' }}>
                <div style={{ flex: 1 }} className="stack">
                  <Skel w="45%" h={12} />
                  <Skel w="70%" h={9} />
                </div>
                <Skel w={90} h={14} />
              </div>
            ))}
          </div>
        ) : (
          <div className="card card-pad">
            {rows.length > 0 && (
              <div className="muted small" style={{ marginBottom: 6 }}>
                {rows.length} waiting · new submissions first, then claims back with the employee
              </div>
            )}
            {rows.length === 0 ? (
              <EmptyState title="You’re all caught up">
                Nothing is waiting at the {STAGE_LABELS[stage]} stage right now.
              </EmptyState>
            ) : (
              rows.map((c) => (
                <div key={c.id} className="list-item" onClick={() => navigate(`/claims/${c.id}`)}>
                  <div className="grow">
                    <div className="title">
                      {vendorOf(c)}{' '}
                      {c.duplicate_flag && <span className="flag">Duplicate?</span>}{' '}
                      {c.vendor_unmatched && <span className="flag">New vendor</span>}
                    </div>
                    <div className="sub">
                      #{c.id} · {c.employee_name ?? `Employee #${c.employee_id}`} · {c.category_name ?? '-'} · bill {c.bill_date ?? '-'} · submitted{' '}
                      {timeAgo(c.submitted_at) || formatDate(c.created_at)}
                    </div>
                  </div>
                  <span className="amount">{money(c.currency, claimTotal(c))}</span>
                  <StatusBadge status={c.status} />
                  <span className="muted" style={{ display: 'flex' }}><Icon name="chevron" size={18} /></span>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </>
  );
}
