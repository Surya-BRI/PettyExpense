import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import type { Claim, ClaimStatus } from '../api/types';
import { useUser } from '../auth/context';
import { Icon } from '../components/Icon';
import { Topbar } from '../components/Layout';
import { EmptyState, ErrorBox, StatusBadge, TableSkeleton } from '../components/ui';
import { PENDING, STAGE_LABELS, STATUS_LABELS, claimTotal, claimWhen, formatDate, isApprover, money, plural, vendorOf } from '../lib/format';
import { useToast } from '../lib/toast';
import { useAsync } from '../lib/useAsync';

type SortKey = 'id' | 'date' | 'employee' | 'vendor' | 'total' | 'status';
const PAGE_SIZES = [25, 50, 100];

const FILTER_KEYS = ['q', 'status', 'stage', 'region', 'category', 'type', 'flagged'] as const;

export function ClaimsPage() {
  const user = useUser();
  const approver = isApprover(user);
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const claims = useAsync(() => (approver ? api.allClaims() : api.myClaims()), [approver]);
  const [sort, setSort] = useState<{ key: SortKey; asc: boolean }>({ key: 'date', asc: false });
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(PAGE_SIZES[0]);
  const toast = useToast();

  const f = Object.fromEntries(FILTER_KEYS.map((k) => [k, params.get(k) ?? ''])) as Record<(typeof FILTER_KEYS)[number], string>;
  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
    setPage(0);
  };

  const all = useMemo(() => claims.data ?? [], [claims.data]);
  const regions = useMemo(() => [...new Set(all.map((c) => c.region_code).filter(Boolean) as string[])].sort(), [all]);
  const categories = useMemo(() => [...new Set(all.map((c) => c.category_name).filter(Boolean) as string[])].sort(), [all]);

  const rows = useMemo(() => {
    const q = f.q.trim().toLowerCase();
    const filtered = all.filter((c) => {
      if (f.status && c.status !== f.status) return false;
      if (f.stage && !(PENDING.includes(c.status) && c.current_stage === f.stage)) return false;
      if (f.region && c.region_code !== f.region) return false;
      if (f.category && (c.category_name || 'Uncategorised') !== f.category) return false;
      if (f.type && c.type !== f.type) return false;
      if (f.flagged && !(c.duplicate_flag || c.vendor_unmatched)) return false;
      if (!q) return true;
      return [String(c.id), c.vendor_name, c.employee_name, c.category_name, c.op_number]
        .filter(Boolean)
        .some((s) => s!.toLowerCase().includes(q));
    });
    const val = (c: Claim): string | number => {
      switch (sort.key) {
        case 'id': return c.id;
        case 'date': return claimWhen(c)?.getTime() ?? 0;
        case 'employee': return (c.employee_name ?? '').toLowerCase();
        case 'vendor': return vendorOf(c).toLowerCase();
        case 'total': return claimTotal(c);
        case 'status': return c.status;
      }
    };
    return filtered.sort((a, b) => {
      const x = val(a), y = val(b);
      const r = x < y ? -1 : x > y ? 1 : 0;
      return sort.asc ? r : -r;
    });
  }, [all, f.q, f.status, f.stage, f.region, f.category, f.type, f.flagged, sort]);

  // Totals per currency for whatever is filtered -- never blended into one number.
  const totals = useMemo(() => {
    const m = new Map<string, number>();
    rows.forEach((c) => m.set(c.currency, (m.get(c.currency) ?? 0) + claimTotal(c)));
    return [...m.entries()];
  }, [rows]);

  const pages = Math.max(1, Math.ceil(rows.length / pageSize));
  const current = Math.min(page, pages - 1);
  const pageRows = rows.slice(current * pageSize, current * pageSize + pageSize);
  const activeFilters = FILTER_KEYS.filter((k) => f[k]).length;

  const th = (key: SortKey, label: string, right = false) => {
    const active = sort.key === key;
    return (
      <th
        className={`sortable${right ? ' r' : ''}${active ? ' sorted' : ''}`}
        onClick={() => setSort((s) => ({ key, asc: s.key === key ? !s.asc : key !== 'date' && key !== 'total' }))}
        aria-sort={active ? (sort.asc ? 'ascending' : 'descending') : 'none'}
      >
        {label}
        <span className="sort" aria-hidden>{active ? (sort.asc ? '▲' : '▼') : '↕'}</span>
      </th>
    );
  };

  return (
    <>
      <Topbar title={approver ? 'All claims' : 'My claims'} crumbs="Claims">
        <button
          className="btn btn-sm"
          disabled={rows.length === 0}
          onClick={() => {
            exportCsv(rows, approver);
            toast.show(`Exported ${plural(rows.length, 'claim')} to CSV`);
          }}
        >
          <Icon name="download" size={16} /> Export CSV
        </button>
        <button className="btn btn-sm" onClick={claims.reload}>
          <Icon name="refresh" size={16} /> Refresh
        </button>
      </Topbar>
      <div className="page stack">
        <div className="filters">
          <div className="grow-input input-wrap">
            <span className="lead">
              <Icon name="search" size={18} />
            </span>
            <input
              className="input"
              type="search"
              aria-label="Search claims"
              placeholder={approver ? 'Search vendor, employee, #id, OP' : 'Search vendor, category, #id'}
              value={f.q}
              onChange={(e) => setFilter('q', e.target.value)}
            />
          </div>
          <select className="select" value={f.status} onChange={(e) => setFilter('status', e.target.value)}>
            <option value="">All statuses</option>
            {(Object.keys(STATUS_LABELS) as ClaimStatus[]).map((s) => (
              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
          </select>
          <select className="select" value={f.stage} onChange={(e) => setFilter('stage', e.target.value)}>
            <option value="">Any stage</option>
            {['hod', 'department_hod', 'accountant', 'finance_manager'].map((s) => (
              <option key={s} value={s}>Waiting: {STAGE_LABELS[s]}</option>
            ))}
          </select>
          {regions.length > 1 && (
            <select className="select" value={f.region} onChange={(e) => setFilter('region', e.target.value)}>
              <option value="">All regions</option>
              {regions.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          )}
          <select className="select" value={f.category} onChange={(e) => setFilter('category', e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="select" value={f.type} onChange={(e) => setFilter('type', e.target.value)}>
            <option value="">All types</option>
            <option value="reimbursement">Reimbursement</option>
            <option value="petty_cash">Petty cash</option>
          </select>
          {approver && (
            <label className="checkbox">
              <input type="checkbox" checked={!!f.flagged} onChange={(e) => setFilter('flagged', e.target.checked ? '1' : '')} />
              Flagged only
            </label>
          )}
          {activeFilters > 0 && (
            <button className="btn btn-ghost btn-sm" onClick={() => { setParams({}, { replace: true }); setPage(0); }}>
              <Icon name="close" size={14} /> Clear {plural(activeFilters, 'filter')}
            </button>
          )}
        </div>

        {claims.data && (
          <div className="row" style={{ gap: 8 }}>
            <span className="strong">{rows.length === all.length ? plural(all.length, 'claim') : `${rows.length} of ${plural(all.length, 'claim')}`}</span>
            {totals.map(([cur, v]) => (
              <span key={cur} className="tag neutral num">{money(cur, v)}</span>
            ))}
          </div>
        )}

        {claims.error && <ErrorBox error={claims.error} onRetry={claims.reload} />}
        {claims.loading && !claims.data ? (
          <TableSkeleton cols={approver ? 8 : 7} />
        ) : (
          <div className="card">
            {rows.length === 0 ? (
              <EmptyState title={all.length === 0 ? 'No claims yet' : 'No claims match these filters'}>
                {all.length === 0
                  ? approver ? 'Claims appear here as soon as employees submit them.' : 'Scan a receipt in the mobile app to create your first claim.'
                  : 'Try removing a filter or searching for something else.'}
              </EmptyState>
            ) : (
              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      {th('id', '#')}
                      {th('date', 'Submitted')}
                      {approver && th('employee', 'Employee')}
                      {th('vendor', 'Vendor')}
                      <th>Category</th>
                      <th>Region</th>
                      {th('total', 'Total', true)}
                      {th('status', 'Status')}
                      <th>Waiting at</th>
                      <th>Flags</th>
                      <th className="chev" aria-label="Open" />
                    </tr>
                  </thead>
                  <tbody>
                    {pageRows.map((c) => (
                      <tr
                        key={c.id}
                        className="clickable"
                        tabIndex={0}
                        onClick={() => navigate(`/claims/${c.id}`)}
                        onKeyDown={(e) => e.key === 'Enter' && navigate(`/claims/${c.id}`)}
                      >
                        <td className="muted num">{c.id}</td>
                        <td>{formatDate(c.submitted_at ?? c.created_at)}</td>
                        {approver && <td className="strong">{c.employee_name ?? `#${c.employee_id}`}</td>}
                        <td className="vendor-cell" title={vendorOf(c)}>{vendorOf(c)}</td>
                        <td>{c.category_name ?? '-'}</td>
                        <td>{c.region_code ?? '-'}</td>
                        <td className="r strong num">{money(c.currency, claimTotal(c))}</td>
                        <td><StatusBadge status={c.status} /></td>
                        <td>{PENDING.includes(c.status) && c.current_stage ? STAGE_LABELS[c.current_stage] : <span className="muted">-</span>}</td>
                        <td>
                          <div className="row" style={{ gap: 4, maxWidth: 104 }}>
                            {c.duplicate_flag && (
                              <span className="flag" data-tip="Same employee, vendor, amount and date as another claim">Dup</span>
                            )}
                            {c.vendor_unmatched && (
                              <span className="flag" data-tip="Vendor not in the vendor list yet (Accountant resolves)">New vendor</span>
                            )}
                            {c.type === 'petty_cash' && <span className="tag" data-tip="Petty cash claim">PC</span>}
                          </div>
                        </td>
                        <td className="chev"><Icon name="chevron" size={18} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {rows.length > 0 && (
              <div className="table-foot">
                <span className="muted small">
                  Showing {current * pageSize + 1}–{Math.min(rows.length, (current + 1) * pageSize)} of {rows.length}
                </span>
                <div className="row" style={{ gap: 8 }}>
                  <label className="row muted small" style={{ gap: 6 }}>
                    Rows
                    <select
                      className="select"
                      style={{ height: 32 }}
                      value={pageSize}
                      onChange={(e) => {
                        setPageSize(Number(e.target.value));
                        setPage(0);
                      }}
                    >
                      {PAGE_SIZES.map((n) => <option key={n} value={n}>{n}</option>)}
                    </select>
                  </label>
                  <button className="btn btn-sm" disabled={current === 0} onClick={() => setPage(current - 1)}>Previous</button>
                  <button className="btn btn-sm" disabled={current >= pages - 1} onClick={() => setPage(current + 1)}>Next</button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

function exportCsv(rows: Claim[], approver: boolean) {
  const header = ['ID', 'Submitted', ...(approver ? ['Employee'] : []), 'Vendor', 'Category', 'Region', 'Type',
    'Currency', 'Amount excl. VAT', 'VAT', 'Total', 'Status', 'Waiting at', 'Bill date', 'OP number', 'Duplicate flag', 'Vendor unmatched'];
  const esc = (v: unknown) => {
    const s = v == null ? '' : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = rows.map((c) =>
    [c.id, formatDate(c.submitted_at ?? c.created_at), ...(approver ? [c.employee_name] : []), c.vendor_name, c.category_name,
      c.region_code, c.type, c.currency, c.amount, c.vat_amount, claimTotal(c), c.status,
      PENDING.includes(c.status) && c.current_stage ? STAGE_LABELS[c.current_stage] : '', c.bill_date, c.op_number,
      c.duplicate_flag ? 'yes' : '', c.vendor_unmatched ? 'yes' : ''].map(esc).join(','),
  );
  // BOM so Excel opens Arabic vendor names correctly.
  const blob = new Blob(['﻿' + [header.join(','), ...lines].join('\r\n')], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `claims-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}
