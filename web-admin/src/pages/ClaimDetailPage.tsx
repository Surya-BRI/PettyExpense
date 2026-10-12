import { useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ApiError, api } from '../api/client';
import type { AuthUser, Claim } from '../api/types';
import { useUser } from '../auth/context';
import { Icon } from '../components/Icon';
import { Topbar } from '../components/Layout';
import { Card, CardSkeleton, ConfirmDialog, EmptyState, ErrorBox, ReceiptImage, Skel, StatusBadge } from '../components/ui';
import { ACTION_LABELS, PENDING, STAGE_LABELS, claimTotal, formatDateTime, isApprover, money, stagesFor, vendorOf } from '../lib/format';
import { useToast } from '../lib/toast';
import { useAsync } from '../lib/useAsync';

export function ClaimDetailPage() {
  const { id } = useParams();
  const claimId = Number(id);
  const user = useUser();
  const approver = isApprover(user);
  const state = useAsync(() => (approver ? api.approvalClaim(claimId) : api.myClaim(claimId)), [claimId, approver]);
  const claim = state.data;
  const notFound = state.error instanceof ApiError && (state.error.status === 404 || state.error.status === 403);

  return (
    <>
      <Topbar
        narrow
        title={claim ? vendorOf(claim) : `Claim #${claimId}`}
        crumbs={
          <>
            <Link to="/claims">Claims</Link> / #{claimId}
          </>
        }
      >
        <Link className="btn btn-sm" to="/claims">
          <Icon name="back" size={16} /> All claims
        </Link>
      </Topbar>
      <div className="page narrow stack">
        {notFound ? (
          <Card>
            <EmptyState title="Claim not found">
              It may have been removed, or you don’t have access to it. <Link to="/claims">Back to claims</Link>
            </EmptyState>
          </Card>
        ) : (
          state.error && <ErrorBox error={state.error} onRetry={state.reload} />
        )}
        {state.loading && !claim ? <DetailSkeleton /> : claim && <Detail claim={claim} user={user} onChanged={state.reload} />}
      </div>
    </>
  );
}

function DetailSkeleton() {
  return (
    <div className="grid-3">
      <div className="stack">
        <section className="card card-pad stack" style={{ gap: 12 }}>
          <Skel w="25%" h={10} />
          <Skel w="55%" h={22} />
          <Skel w="40%" h={16} />
        </section>
        <CardSkeleton rows={3} />
        <CardSkeleton rows={6} />
      </div>
      <section className="card card-pad stack">
        <Skel w="30%" h={14} />
        <Skel h={320} />
      </section>
    </div>
  );
}

function Detail({ claim, user, onChanged }: { claim: Claim; user: AuthUser; onChanged: () => void }) {
  const total = claimTotal(claim);
  // Amount + VAT should equal the total; employees can type anything, so surface a mismatch.
  const computed = Math.round((claim.amount + claim.vat_amount) * 100) / 100;
  const totalsMismatch = Math.abs(computed - total) > 0.01;

  // Only fields that carry a value -- a grid of "-" rows is noise.
  const fields: { label: string; value: ReactNode; wide?: boolean }[] = [
    ...(isApprover(user) ? [{ label: 'Employee', value: claim.employee_name ?? `#${claim.employee_id}` }] : []),
    {
      label: 'Vendor',
      value: (
        <>
          {vendorOf(claim)}
          {claim.vendor_unmatched && <span className="flag" style={{ marginLeft: 8 }}>Not in vendor list</span>}
        </>
      ),
    },
    { label: 'Bill date', value: claim.bill_date },
    { label: 'Category', value: claim.category_name },
    { label: 'Claim type', value: claim.type === 'petty_cash' ? 'Petty cash' : 'Reimbursement' },
    { label: 'Region', value: claim.region_code },
    {
      label: 'Currency',
      value: `${claim.currency}${claim.exchange_rate && claim.exchange_rate !== 1 ? ` (rate ${claim.exchange_rate})` : ''}`,
    },
    { label: 'OP number', value: claim.op_number },
    { label: 'Submitted', value: claim.submitted_at ? formatDateTime(claim.submitted_at) : null },
    { label: 'Decided', value: claim.decided_at ? formatDateTime(claim.decided_at) : null },
    { label: 'Paid', value: claim.paid_at ? formatDateTime(claim.paid_at) : null },
    { label: 'Remarks', value: claim.remarks, wide: true },
  ].filter((f) => f.value !== null && f.value !== undefined && f.value !== '');

  return (
    <div className="grid-3">
      <div className="stack">
        {/* Summary */}
        <section className="card card-pad">
          <div className="row" style={{ alignItems: 'flex-start', gap: 16 }}>
            <div style={{ flex: '1 1 260px', minWidth: 0 }}>
              <div className="muted small">
                Claim #{claim.id} · {claim.region_code ?? '-'}
              </div>
              <h2 style={{ fontSize: 22, letterSpacing: '-0.015em', margin: '6px 0 10px' }}>{vendorOf(claim)}</h2>
              <div className="row" style={{ gap: 6 }}>
                <StatusBadge status={claim.status} />
                <span className="tag">{claim.type === 'petty_cash' ? 'Petty cash' : 'Reimbursement'}</span>
                {claim.category_name && <span className="tag neutral">{claim.category_name}</span>}
              </div>
            </div>
            <div style={{ textAlign: 'right', marginLeft: 'auto' }}>
              <div className="muted small">Total</div>
              <div className="amount-hero num">{money(claim.currency, total)}</div>
            </div>
          </div>
          <div className="money-split">
            <div>
              <span>Amount excl. VAT</span>
              <strong className="num">{money(claim.currency, claim.amount)}</strong>
            </div>
            <div>
              <span>VAT</span>
              <strong className="num">{money(claim.currency, claim.vat_amount)}</strong>
            </div>
            <div>
              <span>Total</span>
              <strong className="num">{money(claim.currency, total)}</strong>
            </div>
          </div>
          {totalsMismatch && (
            <div className="notice small" style={{ marginTop: 12 }}>
              <strong>Totals don’t add up.</strong> Amount + VAT is {money(claim.currency, computed)}, but the total entered is{' '}
              {money(claim.currency, total)}. Check the receipt before approving.
            </div>
          )}
        </section>

        {!!claim.line_items?.length && <LineItems claim={claim} />}

        {claim.stage_sequence.length > 0 && (
          <Card title="Approval progress">
            <Stepper claim={claim} />
          </Card>
        )}

        {(claim.duplicate_warning || claim.duplicate_flag) && (
          <div className="notice">
            <strong>Possible duplicate.</strong>{' '}
            {claim.duplicate_warning?.message ?? 'This employee has another claim with the same vendor, amount and date.'}
            {claim.duplicate_warning?.existing_claim_id && (
              <>
                {' '}
                See <Link to={`/claims/${claim.duplicate_warning.existing_claim_id}`}>claim #{claim.duplicate_warning.existing_claim_id}</Link>.
              </>
            )}
          </div>
        )}

        <Actions claim={claim} user={user} onChanged={onChanged} />

        <Card title="Details">
          <dl className="fields">
            {fields.map((f) => (
              <div key={f.label} className={f.wide ? 'wide' : undefined}>
                <dt>{f.label}</dt>
                <dd>{f.value}</dd>
              </div>
            ))}
          </dl>
        </Card>

        <Card title="History" subtitle="Newest first">
          <History claim={claim} />
        </Card>
      </div>

      {/* Receipt stays in view while scrolling the details. */}
      <div className="sticky-col">
        <Card title="Receipt" subtitle={claim.receipt ? 'Original photo, as uploaded' : undefined}>
          {claim.receipt ? <ReceiptImage url={claim.receipt.image_url} /> : <EmptyState title="No receipt attached" />}
        </Card>
      </div>
    </div>
  );
}

/** Item lines of a "Multiple items" bill: what was bought, its category, and the amount. */
function LineItems({ claim }: { claim: Claim }) {
  const lines = claim.line_items ?? [];
  const sum = lines.reduce((a, l) => a + l.amount, 0);
  const categories = new Set(lines.map((l) => l.category_name).filter(Boolean));
  return (
    <Card
      title="Items"
      subtitle={`${lines.length} item${lines.length === 1 ? '' : 's'}${categories.size > 1 ? ` · ${categories.size} categories` : ''}`}
    >
      <div className="table-wrap items-wrap">
        <table className="data items">
          <thead>
            <tr>
              <th>#</th>
              <th>Item</th>
              <th>Category</th>
              <th className="r">Qty</th>
              <th className="r">Amount</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((l) => (
              <tr key={l.id}>
                <td className="muted num">{l.line_no}</td>
                <td className="item-name">{l.description}</td>
                <td>{l.category_name ?? <span className="muted">-</span>}</td>
                <td className="r num">{l.quantity ?? <span className="muted">-</span>}</td>
                <td className="r num strong">{money(claim.currency, l.amount)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={4} className="strong">Total</td>
              <td className="r num strong">{money(claim.currency, sum)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </Card>
  );
}

function Stepper({ claim }: { claim: Claim }) {
  const seq = claim.stage_sequence;
  const finished = claim.status === 'approved' || claim.status === 'paid';
  const currentIdx = claim.current_stage ? seq.indexOf(claim.current_stage) : -1;
  return (
    <div className="stepper">
      {seq.map((s, i) => {
        const done = finished || (currentIdx >= 0 && i < currentIdx);
        const current = !finished && i === currentIdx && PENDING.includes(claim.status);
        return (
          <div key={s} className={`step${done ? ' done' : ''}${current ? ' current' : ''}`} aria-current={current ? 'step' : undefined}>
            <div className="dot">{done ? '✓' : i + 1}</div>
            {STAGE_LABELS[s] ?? s}
            {current && claim.status === 'disputed' && (
              <div className="small" style={{ color: 'var(--warning-ink)', fontWeight: 500 }}>
                With employee
              </div>
            )}
          </div>
        );
      })}
      <div className={`step${claim.status === 'paid' ? ' done' : ''}${claim.status === 'approved' ? ' current' : ''}`}>
        <div className="dot">{claim.status === 'paid' ? '✓' : seq.length + 1}</div>
        Paid
      </div>
    </div>
  );
}

const HISTORY_DOT: Record<string, string> = {
  approve: 'var(--success)',
  paid: 'var(--blue)',
  reject: 'var(--danger)',
  dispute: 'var(--orange)',
  submitted: 'var(--bright-blue)',
};

function History({ claim }: { claim: Claim }) {
  const items = [...(claim.history ?? [])].reverse();
  if (items.length === 0) return <EmptyState title="No history yet" />;
  return (
    <div className="timeline">
      {items.map((h) => {
        const who = h.actor_id === claim.employee_id ? claim.employee_name ?? 'Employee' : STAGE_LABELS[h.stage ?? ''] ?? 'Approver';
        return (
          <div key={h.id} className="tl-item">
            <span className="tl-dot" style={{ background: HISTORY_DOT[h.action] ?? 'var(--line-strong)' }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div>
                <span className="strong">{who}</span> {ACTION_LABELS[h.action] ?? h.action} this claim
                {h.stage && h.stage !== 'employee' && <span className="muted"> · {STAGE_LABELS[h.stage] ?? h.stage} stage</span>}
              </div>
              {h.remarks && (
                <div className="small" style={{ marginTop: 2, color: 'var(--text-2)' }}>
                  “{h.remarks}”
                </div>
              )}
            </div>
            <div className="muted small" style={{ whiteSpace: 'nowrap' }}>
              {formatDateTime(h.created_at)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

type PendingAction = { title: string; message: string; label: string; tone: 'primary' | 'danger' | 'blue'; done: string; run: () => Promise<unknown> };

/** Only the actions the backend will actually accept from this user right now. */
function Actions({ claim, user, onChanged }: { claim: Claim; user: AuthUser; onChanged: () => void }) {
  const toast = useToast();
  const [comment, setComment] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [confirm, setConfirm] = useState<PendingAction | null>(null);

  const pending = PENDING.includes(claim.status);
  const myStage = pending && claim.current_stage != null && stagesFor(user.role).includes(claim.current_stage);
  const canPay = claim.status === 'approved' && (user.role === 'finance_manager' || user.role === 'admin');
  const canResolveVendor =
    pending && claim.vendor_unmatched && claim.current_stage === 'accountant' && (user.role === 'accountant' || user.role === 'admin');
  const isOwner = user.id === claim.employee_id;
  const needsJustification = claim.current_stage === 'accountant' && (claim.duplicate_flag || !!claim.duplicate_warning);

  if (!myStage && !canPay && !canResolveVendor && !(isOwner && (claim.status === 'draft' || claim.status === 'disputed'))) {
    return null;
  }

  const run = async (done: string, fn: () => Promise<unknown>) => {
    setBusy(true);
    setError(undefined);
    try {
      await fn();
      toast.show(done);
      setComment('');
      setConfirm(null);
      onChanged();
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Action failed';
      setError(msg);
      toast.show(msg, 'error');
      setConfirm(null);
    } finally {
      setBusy(false);
    }
  };
  const c = comment.trim();
  const total = money(claim.currency, claimTotal(claim));

  return (
    <Card title="Your action" subtitle={myStage ? `Waiting at the ${STAGE_LABELS[claim.current_stage!]} stage` : undefined}>
      <div className="stack" style={{ gap: 12 }}>
        {canResolveVendor && <VendorResolver claim={claim} busy={busy} run={run} />}
        {(myStage || canPay) && (
          <label className="field">
            Comment
            <textarea
              className="textarea"
              placeholder={needsJustification ? 'Required: justify approving a possible duplicate' : 'Required to dispute or reject; optional to approve'}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </label>
        )}
        <div className="row">
          {myStage && (
            <>
              <button
                className="btn btn-primary"
                disabled={busy || (needsJustification && !c)}
                onClick={() => run('Claim approved', () => api.approve(claim.id, c))}
              >
                <Icon name="check" size={16} /> Approve
              </button>
              <button
                className="btn"
                disabled={busy || !c}
                title={!c ? 'Add a comment explaining what to fix' : undefined}
                onClick={() =>
                  setConfirm({
                    title: 'Send back to the employee?',
                    message: `The employee will be asked to correct this ${total} claim and resubmit it. It comes back to your stage afterwards.`,
                    label: 'Send back',
                    tone: 'primary',
                    done: 'Claim sent back to the employee',
                    run: () => api.dispute(claim.id, c),
                  })
                }
              >
                <Icon name="undo" size={16} /> Dispute
              </button>
              <button
                className="btn btn-danger"
                disabled={busy || !c}
                title={!c ? 'Add a comment with the reason' : undefined}
                onClick={() =>
                  setConfirm({
                    title: 'Reject this claim?',
                    message: `Rejecting ends the approval for this ${total} claim. The employee is notified with your comment. This can’t be undone.`,
                    label: 'Reject claim',
                    tone: 'danger',
                    done: 'Claim rejected',
                    run: () => api.reject(claim.id, c),
                  })
                }
              >
                <Icon name="close" size={16} /> Reject
              </button>
            </>
          )}
          {canPay && (
            <button
              className="btn btn-blue"
              disabled={busy}
              onClick={() =>
                setConfirm({
                  title: 'Mark as paid?',
                  message: `Confirm that ${total} has been paid to ${claim.employee_name ?? 'the employee'}. They will be notified.`,
                  label: 'Mark paid',
                  tone: 'blue',
                  done: 'Claim marked as paid',
                  run: () => api.markPaid(claim.id, c),
                })
              }
            >
              <Icon name="pay" size={16} /> Mark paid
            </button>
          )}
          {isOwner && claim.status === 'draft' && (
            <button className="btn btn-primary" disabled={busy} onClick={() => run('Claim submitted for approval', () => api.submitDraft(claim.id))}>
              <Icon name="send" size={16} /> Submit draft
            </button>
          )}
          {isOwner && claim.status === 'disputed' && (
            <button className="btn btn-primary" disabled={busy} onClick={() => run('Claim resubmitted', () => api.resubmit(claim.id))}>
              <Icon name="send" size={16} /> Resubmit corrected claim
            </button>
          )}
        </div>
        {error && <div className="error-box" role="alert"><span>{error}</span></div>}
      </div>
      {confirm && (
        <ConfirmDialog
          title={confirm.title}
          message={confirm.message}
          confirmLabel={confirm.label}
          tone={confirm.tone}
          busy={busy}
          onCancel={() => setConfirm(null)}
          onConfirm={() => run(confirm.done, confirm.run)}
        />
      )}
    </Card>
  );
}

function VendorResolver({
  claim,
  busy,
  run,
}: {
  claim: Claim;
  busy: boolean;
  run: (done: string, fn: () => Promise<unknown>) => void;
}) {
  const vendors = useAsync(() => api.vendors(), []);
  const [vendorId, setVendorId] = useState('');
  return (
    <div className="notice">
      <div className="strong" style={{ marginBottom: 10 }}>
        “{claim.vendor_name}” isn’t in the vendor list yet
      </div>
      <div className="row">
        <select className="select" value={vendorId} onChange={(e) => setVendorId(e.target.value)} disabled={vendors.loading} aria-label="Existing vendor">
          <option value="">{vendors.loading ? 'Loading vendors…' : 'Link to an existing vendor…'}</option>
          {vendors.data?.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}
            </option>
          ))}
        </select>
        <button
          className="btn btn-sm"
          disabled={busy || !vendorId}
          onClick={() => run('Vendor linked', () => api.resolveVendor(claim.id, { vendor_id: Number(vendorId) }))}
        >
          Link
        </button>
        <span className="muted small">or</span>
        <button
          className="btn btn-sm"
          disabled={busy}
          onClick={() => run('New vendor confirmed', () => api.resolveVendor(claim.id, { create_new: true }))}
        >
          Confirm as new vendor
        </button>
      </div>
    </div>
  );
}
