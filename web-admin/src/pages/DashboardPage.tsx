import { useMemo, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { ActivityItem, Claim } from '../api/types';
import { useUser } from '../auth/context';
import { Icon } from '../components/Icon';
import { Topbar } from '../components/Layout';
import { BarList, Card, CardSkeleton, ColumnChart, EmptyState, ErrorBox, Kpi, KpiSkeletons, Skel, StatusBadge, type BarDatum } from '../components/ui';
import {
  ACTION_LABELS,
  PENDING,
  STAGE_LABELS,
  STATUS_LABELS,
  claimTotal,
  claimWhen,
  compact,
  formatDate,
  isApprover,
  money,
  plural,
  timeAgo,
  vendorOf,
} from '../lib/format';
import { useAsync } from '../lib/useAsync';

type Period = '30' | '90' | 'year' | 'all';
const PERIODS: { value: Period; label: string }[] = [
  { value: '30', label: 'Last 30 days' },
  { value: '90', label: 'Last 90 days' },
  { value: 'year', label: 'This year' },
  { value: 'all', label: 'All time' },
];

function inPeriod(c: Claim, period: Period, now: Date) {
  if (period === 'all') return true;
  const d = claimWhen(c);
  if (!d) return false;
  if (period === 'year') return d.getFullYear() === now.getFullYear();
  return now.getTime() - d.getTime() <= Number(period) * 86_400_000;
}

const sum = (xs: Claim[]) => xs.reduce((a, c) => a + claimTotal(c), 0);
const isSpend = (c: Claim) => c.status !== 'draft' && c.status !== 'rejected';

export function DashboardPage() {
  const user = useUser();
  const approver = isApprover(user);
  const navigate = useNavigate();
  const claims = useAsync(() => (approver ? api.allClaims() : api.myClaims()), [approver]);
  const activity = useAsync(() => (approver ? api.activity(30) : Promise.resolve(null)), [approver]);

  const [period, setPeriod] = useState<Period>('all');
  const [region, setRegion] = useState('');
  const [currencyChoice, setCurrency] = useState('');

  const all = useMemo(() => claims.data ?? [], [claims.data]);
  const currencies = useMemo(() => [...new Set(all.map((c) => c.currency))].sort(), [all]);
  const regions = useMemo(() => [...new Set(all.map((c) => c.region_code).filter(Boolean) as string[])].sort(), [all]);
  // Default to whichever currency most claims use; money is never summed across currencies.
  const currency = useMemo(() => {
    if (currencyChoice && currencies.includes(currencyChoice)) return currencyChoice;
    const counts = new Map<string, number>();
    all.forEach((c) => counts.set(c.currency, (counts.get(c.currency) ?? 0) + 1));
    return [...counts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'AED';
  }, [all, currencies, currencyChoice]);

  const [now] = useState(() => new Date());
  const scoped = useMemo(
    () => all.filter((c) => c.currency === currency && (!region || c.region_code === region)),
    [all, currency, region],
  );
  const shown = useMemo(() => scoped.filter((c) => inPeriod(c, period, now)), [scoped, period, now]);

  const openClaim = (id: number) => navigate(`/claims/${id}`);
  const toClaims = (params: Record<string, string>) =>
    navigate(`/claims?${new URLSearchParams({ ...params, ...(region ? { region } : {}) })}`);

  const refresh = () => {
    claims.reload();
    activity.reload();
  };

  const periodLabel = PERIODS.find((p) => p.value === period)?.label ?? '';

  const statusCard = (
    <Card title="Claims by status" subtitle="Number of claims · click a bar to see them">
      <BarList
        data={(Object.keys(STATUS_LABELS) as (keyof typeof STATUS_LABELS)[])
          .map((s) => {
            const g = shown.filter((c) => c.status === s);
            return {
              label: STATUS_LABELS[s],
              value: g.length,
              display: String(g.length),
              tip: `${plural(g.length, 'claim')} · ${money(currency, sum(g))}`,
              onClick: () => toClaims({ status: s }),
            };
          })
          .filter((d) => d.value > 0)}
      />
    </Card>
  );

  const stageCard = (
    <Card title="Where claims are waiting" subtitle="Pending claims per approval stage · click a bar to see them">
      <BarList
        empty="Nothing is waiting for approval."
        data={['hod', 'department_hod', 'accountant', 'finance_manager']
          .map((st) => {
            const g = shown.filter((c) => PENDING.includes(c.status) && c.current_stage === st);
            const disputed = g.filter((c) => c.status === 'disputed').length;
            return {
              label: STAGE_LABELS[st],
              value: g.length,
              display: String(g.length),
              tip: `${money(currency, sum(g))}${disputed ? ` · ${disputed} back with employee` : ''}`,
              onClick: () => toClaims({ stage: st }),
            };
          })
          .filter((d) => d.value > 0)}
      />
    </Card>
  );

  const latestCard = <Latest claims={shown} approver={approver} onOpen={openClaim} onAll={() => navigate('/claims')} />;

  return (
    <>
      <Topbar title={approver ? 'Company overview' : 'My overview'} crumbs="Dashboard">
        <button className="btn btn-sm" onClick={refresh}>
          <Icon name="refresh" size={16} /> Refresh
        </button>
      </Topbar>
      <div className="page stack">
        <div className="filters">
          <select className="select" value={period} onChange={(e) => setPeriod(e.target.value as Period)} aria-label="Period">
            {PERIODS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
          <select className="select" value={region} onChange={(e) => setRegion(e.target.value)} aria-label="Region">
            <option value="">All regions</option>
            {regions.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          {currencies.length > 0 && (
            <div className="seg" role="radiogroup" aria-label="Currency">
              {currencies.map((c) => (
                <button key={c} role="radio" aria-checked={c === currency} className={c === currency ? 'on' : undefined} onClick={() => setCurrency(c)}>
                  {c}
                </button>
              ))}
            </div>
          )}
          <span className="muted small hint">
            {shown.length} of {plural(all.length, 'claim')} in view
          </span>
        </div>

        {claims.error && <ErrorBox error={claims.error} onRetry={claims.reload} />}

        {claims.loading && !claims.data ? (
          <>
            <Section title="At a glance">
              <KpiSkeletons />
            </Section>
            <Section title="Needs action">
              <div className="grid-2">
                <CardSkeleton />
                <CardSkeleton />
              </div>
            </Section>
          </>
        ) : (
          <>
            {/* 1. Headline numbers */}
            <Section title="At a glance" hint={`${periodLabel} · ${region || 'All regions'} · ${currency}`}>
              <Kpis claims={shown} currency={currency} />
            </Section>

            {/* 2. What needs someone to act, first */}
            <Section title="Needs action" hint={approver ? 'Flagged claims and where the queue is waiting' : 'Your claims that need you'}>
              <div className="grid-2">
                <Attention claims={shown} approver={approver} onOpen={openClaim} />
                {approver ? stageCard : latestCard}
              </div>
            </Section>

            {/* 3. Recent movement */}
            {approver ? (
              <Section title="Recent" hint="Latest workflow events and submissions">
                <div className="grid-2">
                  <Activity state={activity} onOpen={openClaim} />
                  {latestCard}
                </div>
              </Section>
            ) : (
              <Section title="Progress" hint="Where your claims are in the approval chain">
                <div className="grid-2">
                  {statusCard}
                  {stageCard}
                </div>
              </Section>
            )}

            {/* 4. Spending breakdowns */}
            <Section title="Spending" hint="Excludes drafts and rejected claims">
              <div className="grid-2">
                <Card title="Spend by category" subtitle="Claimed total per category · click a bar to see them">
                  <BarList data={categoryBars(shown, currency, (cat) => toClaims({ category: cat }))} />
                </Card>
                <Card title="Monthly spend" subtitle="Last 6 months by submission date · not affected by the period filter">
                  <ColumnChart data={monthly(scoped, currency, now)} />
                </Card>
              </div>
            </Section>

            {/* 5. People (approvers only) */}
            {approver && (
              <Section title="People & status" hint="Who is claiming and how claims are progressing">
                <div className="grid-2">
                  <TopEmployees claims={shown} currency={currency} />
                  {statusCard}
                </div>
              </Section>
            )}
          </>
        )}
      </div>
    </>
  );
}

/** A labelled dashboard band: small uppercase title, optional hint, and a hairline rule. */
function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <section className="section" aria-label={title}>
      <div className="section-head">
        <h2>{title}</h2>
        {hint && <p>{hint}</p>}
      </div>
      {children}
    </section>
  );
}

function Kpis({ claims, currency }: { claims: Claim[]; currency: string }) {
  const spend = claims.filter(isSpend);
  const pending = claims.filter((c) => PENDING.includes(c.status));
  const disputed = pending.filter((c) => c.status === 'disputed').length;
  const approved = claims.filter((c) => c.status === 'approved');
  const paid = claims.filter((c) => c.status === 'paid');
  const rejected = claims.filter((c) => c.status === 'rejected');
  const drafts = claims.filter((c) => c.status === 'draft').length;
  return (
    <div className="kpis">
      <Kpi label="Total claimed" value={money(currency, sum(spend))} detail={`${plural(spend.length, 'claim')}${drafts ? ` · ${plural(drafts, 'draft')}` : ''}`} accent="var(--bright-blue)" />
      <Kpi label="Pending approval" value={money(currency, sum(pending))} detail={`${plural(pending.length, 'claim')}${disputed ? ` · ${disputed} disputed` : ''}`} accent="var(--orange)" />
      <Kpi label="Approved, unpaid" value={money(currency, sum(approved))} detail={`${plural(approved.length, 'claim')} awaiting payment`} accent="var(--success)" />
      <Kpi label="Paid out" value={money(currency, sum(paid))} detail={plural(paid.length, 'claim')} accent="var(--blue)" />
      <Kpi label="Rejected" value={money(currency, sum(rejected))} detail={plural(rejected.length, 'claim')} accent="var(--danger)" />
    </div>
  );
}

function categoryBars(claims: Claim[], currency: string, onClick: (cat: string) => void): BarDatum[] {
  const totals = new Map<string, { total: number; n: number }>();
  claims.filter(isSpend).forEach((c) => {
    const k = c.category_name || 'Uncategorised';
    const t = totals.get(k) ?? { total: 0, n: 0 };
    totals.set(k, { total: t.total + claimTotal(c), n: t.n + 1 });
  });
  const sorted = [...totals.entries()].sort((a, b) => b[1].total - a[1].total);
  const bars: BarDatum[] = sorted.slice(0, 6).map(([k, v]) => ({
    label: k,
    value: v.total,
    display: money(currency, v.total),
    tip: plural(v.n, 'claim'),
    onClick: () => onClick(k),
  }));
  // Long tail folds into one "Other" bar instead of growing the list.
  const rest = sorted.slice(6);
  if (rest.length) {
    const total = rest.reduce((a, [, v]) => a + v.total, 0);
    bars.push({ label: 'Other', value: total, display: money(currency, total), tip: `${rest.length} more categories` });
  }
  return bars;
}

function monthly(claims: Claim[], currency: string, now: Date) {
  const months = Array.from({ length: 6 }, (_, i) => new Date(now.getFullYear(), now.getMonth() - 5 + i, 1));
  return months.map((m, i) => {
    const g = claims.filter((c) => {
      const d = claimWhen(c);
      return isSpend(c) && d && d.getFullYear() === m.getFullYear() && d.getMonth() === m.getMonth();
    });
    const total = sum(g);
    const name = m.toLocaleString('en-GB', { month: 'short' });
    return {
      label: name,
      value: total,
      tip: `${m.toLocaleString('en-GB', { month: 'long', year: 'numeric' })}: ${plural(g.length, 'claim')} · ${money(currency, total)}`,
      top: i === months.length - 1 && total > 0 ? compact(total) : undefined,
    };
  });
}

function TopEmployees({ claims, currency }: { claims: Claim[]; currency: string }) {
  const rows = useMemo(() => {
    const by = new Map<string, Claim[]>();
    claims
      .filter((c) => c.status !== 'draft')
      .forEach((c) => {
        const k = c.employee_name || `Employee #${c.employee_id}`;
        by.set(k, [...(by.get(k) ?? []), c]);
      });
    return [...by.entries()]
      .map(([name, cs]) => ({
        name,
        n: cs.length,
        total: sum(cs.filter(isSpend)),
        pending: sum(cs.filter((c) => PENDING.includes(c.status))),
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 8);
  }, [claims]);

  return (
    <Card title="Top employees" subtitle="By claimed total, excluding rejected">
      {rows.length === 0 ? (
        <EmptyState title="No submitted claims for this filter" />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Employee</th>
                <th className="r">Claims</th>
                <th className="r">Claimed</th>
                <th className="r">Pending</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.name} style={{ cursor: 'default' }}>
                  <td className="strong">{r.name}</td>
                  <td className="r num">{r.n}</td>
                  <td className="r num">{money(currency, r.total)}</td>
                  <td className="r num muted">{r.pending ? money(currency, r.pending) : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

function Attention({ claims, approver, onOpen }: { claims: Claim[]; approver: boolean; onOpen: (id: number) => void }) {
  const open = claims.filter((c) => PENDING.includes(c.status));
  const groups: { label: string; items: Claim[] }[] = approver
    ? [
        { label: 'Possible duplicates', items: open.filter((c) => c.duplicate_flag) },
        { label: 'Unmatched vendors', items: open.filter((c) => c.vendor_unmatched) },
        { label: 'Disputed, with employee', items: open.filter((c) => c.status === 'disputed') },
      ]
    : [
        { label: 'Sent back to you', items: open.filter((c) => c.status === 'disputed') },
        { label: 'Drafts not submitted', items: claims.filter((c) => c.status === 'draft') },
      ];
  const flagged = [...new Map(groups.flatMap((g) => g.items).map((c) => [c.id, c])).values()];

  return (
    <Card title="Needs attention" subtitle={approver ? 'Open claims carrying a flag' : 'Your claims that need an action'}>
      <div className="row" style={{ marginBottom: 10 }}>
        {groups.map((g) => (
          <span key={g.label} className={g.items.length ? 'flag' : 'tag'} style={{ padding: '6px 10px', fontSize: 12 }}>
            {g.items.length} {g.label}
          </span>
        ))}
      </div>
      {flagged.length === 0 ? (
        <EmptyState title="All clear">Nothing needs attention right now.</EmptyState>
      ) : flagged.slice(0, 6).map((c) => <ClaimLine key={c.id} c={c} approver={approver} onOpen={onOpen} />)}
    </Card>
  );
}

function ClaimLine({ c, approver, onOpen }: { c: Claim; approver: boolean; onOpen: (id: number) => void }) {
  return (
    <div className="list-item" onClick={() => onOpen(c.id)}>
      <div className="grow">
        <div className="title">{vendorOf(c)}</div>
        <div className="sub">
          {[`#${c.id}`, approver ? c.employee_name : null, c.category_name, formatDate(c.submitted_at ?? c.created_at)]
            .filter(Boolean)
            .join(' · ')}
        </div>
      </div>
      <span className="amount">{money(c.currency, claimTotal(c))}</span>
      <StatusBadge status={c.status} />
    </div>
  );
}

function Latest({ claims, approver, onOpen, onAll }: { claims: Claim[]; approver: boolean; onOpen: (id: number) => void; onAll: () => void }) {
  const latest = [...claims].sort((a, b) => (claimWhen(b)?.getTime() ?? 0) - (claimWhen(a)?.getTime() ?? 0)).slice(0, 8);
  return (
    <Card
      title="Latest claims"
      right={
        <button className="btn btn-sm" onClick={onAll}>
          View all
        </button>
      }
    >
      {latest.length === 0 ? <EmptyState title="No claims for this filter" /> : latest.map((c) => <ClaimLine key={c.id} c={c} approver={approver} onOpen={onOpen} />)}
    </Card>
  );
}

const ACTION_STYLE: Record<string, { color: string }> = {
  approve: { color: 'var(--success)' },
  dispute: { color: 'var(--orange)' },
  reject: { color: 'var(--danger)' },
  submitted: { color: 'var(--bright-blue)' },
  paid: { color: 'var(--blue)' },
  vendor_resolved: { color: 'var(--blue)' },
};

function Activity({
  state,
  onOpen,
}: {
  state: { data: ActivityItem[] | null | undefined; error?: Error; loading: boolean };
  onOpen: (id: number) => void;
}) {
  return (
    <Card title="Recent activity" subtitle="Every approval-workflow event, newest first">
      {state.loading && state.data === undefined ? (
        <div className="stack" style={{ gap: 14 }}>
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="row" style={{ flexWrap: 'nowrap' }}>
              <Skel w={32} h={32} />
              <div style={{ flex: 1 }} className="stack">
                <Skel w="65%" h={11} />
                <Skel w="35%" h={9} />
              </div>
            </div>
          ))}
        </div>
      ) : state.error ? (
        <EmptyState title="Couldn’t load activity">{state.error.message}</EmptyState>
      ) : state.data === null ? (
        <EmptyState title="Activity feed not enabled yet">
          It turns on once the backend with <code>GET /api/admin/activity</code> is deployed.
        </EmptyState>
      ) : !state.data?.length ? (
        <EmptyState title="No activity yet" />
      ) : (
        state.data.slice(0, 12).map((a) => {
          const s = ACTION_STYLE[a.action] ?? { color: 'var(--line-strong)' };
          return (
            <div key={a.id} className="list-item" onClick={() => onOpen(a.transaction_id)} style={{ alignItems: 'flex-start' }}>
              <span className="action-mark" style={{ background: s.color }} aria-hidden />
              <div className="grow">
                <div style={{ whiteSpace: 'normal' }}>
                  <span className="strong">{a.actor_name ?? 'Someone'}</span> {ACTION_LABELS[a.action] ?? a.action} claim #{a.transaction_id}
                  {a.vendor_name ? <span className="muted"> · {a.vendor_name}</span> : null}
                </div>
                <div className="sub">
                  {[a.stage && a.stage !== 'employee' ? STAGE_LABELS[a.stage] ?? a.stage : null,
                    a.total_amount != null && a.currency ? money(a.currency, a.total_amount) : null,
                    timeAgo(a.created_at)]
                    .filter(Boolean)
                    .join(' · ')}
                </div>
                {a.comment?.trim() && (
                  <div className="small" style={{ fontStyle: 'italic', marginTop: 2 }}>
                    “{a.comment.trim()}”
                  </div>
                )}
              </div>
            </div>
          );
        })
      )}
    </Card>
  );
}
