import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { AppNotification } from '../api/types';
import { Topbar } from '../components/Layout';
import { EmptyState, ErrorBox, Skel } from '../components/ui';
import { formatDateTime, timeAgo } from '../lib/format';
import { useToast } from '../lib/toast';
import { useAsync } from '../lib/useAsync';

export function NotificationsPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const list = useAsync(() => api.notifications(100), []);
  const items = list.data ?? [];
  const unread = items.filter((n) => n.status !== 'read').length;

  const open = async (n: AppNotification) => {
    if (n.status !== 'read') {
      await api.markRead(n.id).catch(() => undefined);
    }
    if (n.transaction_id) navigate(`/claims/${n.transaction_id}`);
    else list.reload();
  };

  return (
    <>
      <Topbar narrow title="Notifications" crumbs={unread ? `${unread} unread` : 'All caught up'}>
        <button
          className="btn btn-sm"
          disabled={!unread}
          onClick={async () => {
            try {
              const { marked } = await api.markAllRead();
              toast.show(marked ? `Marked ${marked} as read` : 'Everything was already read', 'info');
              list.reload();
            } catch (e) {
              toast.show(e instanceof Error ? e.message : 'Could not mark as read', 'error');
            }
          }}
        >
          Mark all read
        </button>
      </Topbar>
      <div className="page narrow stack">
        {list.error && <ErrorBox error={list.error} onRetry={list.reload} />}
        {list.loading && !list.data ? (
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
            {items.length === 0 ? (
              <EmptyState title="No notifications yet">
                You’ll be notified here when a claim needs you or changes status.
              </EmptyState>
            ) : (
              items.map((n) => (
                <div key={n.id} className="list-item" onClick={() => open(n)} style={{ alignItems: 'flex-start' }}>
                  <span className="action-mark" style={{ background: n.status === 'read' ? 'var(--line-strong)' : 'var(--blue)' }} aria-hidden />
                  <div className="grow">
                    <div style={{ whiteSpace: 'normal', fontWeight: n.status === 'read' ? 400 : 600 }}>{n.message ?? n.type}</div>
                    <div className="sub" title={formatDateTime(n.sent_at)}>
                      {timeAgo(n.sent_at)}
                      {n.transaction_id ? ` · claim #${n.transaction_id}` : ''}
                    </div>
                  </div>
                  {n.status !== 'read' && (
                    <span aria-label="Unread" style={{ background: 'var(--orange)', width: 8, height: 8, marginTop: 8, flexShrink: 0 }} />
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </>
  );
}
