import { useEffect, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { api } from '../api/client';
import type { ClaimStatus } from '../api/types';
import { STATUS_LABELS } from '../lib/format';
import { Icon } from './Icon';


export function StatusBadge({ status }: { status: ClaimStatus }) {
  return <span className={`badge b-${status}`}>{STATUS_LABELS[status] ?? status}</span>;
}

export function Card({
  title,
  subtitle,
  right,
  children,
}: {
  title?: string;
  subtitle?: string;
  right?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="card card-pad">
      {title && (
        <div className="card-head">
          <div>
            <h3>{title}</h3>
            {subtitle && <p>{subtitle}</p>}
          </div>
          {right && <div className="right">{right}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export const Spinner = () => (
  <div className="center" role="status" aria-label="Loading">
    <div className="spinner" />
  </div>
);

/** Inline, one-line "nothing here" message inside a card. */
export const Empty = ({ children }: { children: ReactNode }) => <div className="empty">{children}</div>;

/** Centered empty state -- for whole panels and pages. */
export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="empty-state">
      <div className="empty-title">{title}</div>
      {children && <div className="small">{children}</div>}
    </div>
  );
}

export const ErrorBox = ({ error, onRetry }: { error: Error; onRetry?: () => void }) => (
  <div className="error-box" role="alert">
    <span style={{ flex: 1 }}>{error.message}</span>
    {onRetry && (
      <button className="btn btn-sm" onClick={onRetry}>
        Try again
      </button>
    )}
  </div>
);

// ---------------------------------------------------------------------------
// Skeletons -- same footprint as the loaded content, so the page doesn't jump.
// ---------------------------------------------------------------------------

export const Skel = ({ w = '100%', h = 12 }: { w?: number | string; h?: number }) => (
  <div className="skel" style={{ width: w, height: h }} aria-hidden />
);

export function KpiSkeletons({ count = 5 }: { count?: number }) {
  return (
    <div className="kpis" aria-busy>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="card kpi">
          <Skel w="45%" h={12} />
          <Skel w="70%" h={26} />
          <Skel w="40%" h={10} />
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <section className="card card-pad" aria-busy>
      <div className="stack" style={{ gap: 14 }}>
        <Skel w="35%" h={14} />
        {Array.from({ length: rows }, (_, i) => (
          <div key={i} className="row" style={{ flexWrap: 'nowrap' }}>
            <Skel w="22%" h={10} />
            <Skel w={`${70 - i * 9}%`} h={8} />
          </div>
        ))}
      </div>
    </section>
  );
}

export function TableSkeleton({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="card" aria-busy style={{ padding: 16 }}>
      <div className="stack" style={{ gap: 16 }}>
        {Array.from({ length: rows }, (_, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: 16 }}>
            {Array.from({ length: cols }, (_, j) => (
              <Skel key={j} h={10} w={`${60 + ((i + j) % 3) * 15}%`} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// KPI tile & charts
// ---------------------------------------------------------------------------

export function Kpi({ label, value, detail, accent }: { label: string; value: string; detail: string; accent: string }) {
  return (
    <div className="card kpi" style={{ ['--accent' as string]: accent }}>
      <div className="kpi-top">
        <span className="label">{label}</span>
      </div>
      <div className="value num" title={value}>
        {value}
      </div>
      <div className="detail">{detail}</div>
    </div>
  );
}

export interface BarDatum {
  label: string;
  value: number;
  display: string;
  tip: string;
  onClick?: () => void;
}

/** Horizontal bars, one hue (magnitude only) -- the card title names the measure. */
export function BarList({ data, empty = 'No claims for this filter.' }: { data: BarDatum[]; empty?: string }) {
  if (data.length === 0) return <EmptyState title={empty} />;
  const max = Math.max(...data.map((d) => d.value), 0);
  return (
    <div className="bars">
      {data.map((d) => (
        <div
          key={d.label}
          className="bar-row"
          data-tip={d.tip}
          onClick={d.onClick}
          onKeyDown={(e) => d.onClick && (e.key === 'Enter' || e.key === ' ') && d.onClick()}
          role={d.onClick ? 'button' : undefined}
          tabIndex={d.onClick ? 0 : undefined}
          style={{ cursor: d.onClick ? 'pointer' : undefined }}
        >
          <span className="bar-label">{d.label}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${max > 0 ? (d.value / max) * 100 : 0}%` }} />
          </div>
          <span className="bar-value">{d.display}</span>
        </div>
      ))}
    </div>
  );
}

export interface ColDatum {
  label: string;
  value: number;
  tip: string;
  top?: string;
}

/** Vertical columns for change over time; only the latest column is direct-labeled. */
export function ColumnChart({ data }: { data: ColDatum[] }) {
  const max = Math.max(...data.map((d) => d.value), 0);
  if (max <= 0) return <EmptyState title="No claims in this window" />;
  return (
    <div role="img" aria-label={data.map((d) => d.tip).join('; ')}>
      <div className="cols">
        {data.map((d) => (
          <div key={d.label} className="col" data-tip={d.tip}>
            {d.top && <div className="col-top num">{d.top}</div>}
            <div className="col-fill" style={{ height: `${(d.value / max) * 100}%`, minHeight: d.value > 0 ? 3 : 0 }} />
          </div>
        ))}
      </div>
      <div className="col-labels">
        {data.map((d) => (
          <span key={d.label}>{d.label}</span>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Receipt image
// ---------------------------------------------------------------------------

/** Receipt photo: presigned S3 URLs load directly; the backend proxy path needs the bearer token. */
export function ReceiptImage({ url }: { url: string }) {
  const [src, setSrc] = useState<string>();
  const [failed, setFailed] = useState(false);
  const [zoom, setZoom] = useState(false);

  useEffect(() => {
    let objectUrl: string | undefined;
    let cancelled = false;
    api
      .receiptImage(url)
      .then((s) => {
        if (s.startsWith('blob:')) objectUrl = s;
        if (!cancelled) setSrc(s);
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [url]);

  useEffect(() => {
    if (!zoom) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setZoom(false);
    window.addEventListener('keydown', onKey);
    // Stop the page behind from scrolling while the photo is open.
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [zoom]);

  if (failed) return <EmptyState title="Receipt image unavailable">It could not be loaded from storage.</EmptyState>;
  if (!src) return <Skel h={320} />;
  return (
    <>
      <img className="receipt-img" src={src} alt="Receipt" onClick={() => setZoom(true)} onError={() => setFailed(true)} />
      <div className="muted small" style={{ marginTop: 8 }}>Click the image to view full size.</div>
      {zoom &&
        // Portalled to <body>: rendered inside the (sticky) receipt column it would be trapped in that
        // column's stacking context, and page elements like the top bar would paint over it.
        createPortal(
          <div className="lightbox" onClick={() => setZoom(false)} role="dialog" aria-modal="true" aria-label="Receipt, full size">
            <button
              type="button"
              className="lightbox-close"
              onClick={() => setZoom(false)}
              aria-label="Close"
              title="Close (Esc)"
            >
              <Icon name="close" size={22} />
            </button>
            <img src={src} alt="Receipt, full size" onClick={(e) => e.stopPropagation()} />
            <div className="lightbox-hint">Press Esc or click outside the photo to close</div>
          </div>,
          document.body,
        )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Confirmation dialog
// ---------------------------------------------------------------------------

export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  tone = 'primary',
  busy,
  onConfirm,
  onCancel,
}: {
  title: string;
  message: ReactNode;
  confirmLabel: string;
  tone?: 'primary' | 'danger' | 'blue';
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const confirmRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    confirmRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onCancel();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onCancel]);

  const cls = tone === 'danger' ? 'btn-danger-solid' : tone === 'blue' ? 'btn-blue' : 'btn-primary';
  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" onClick={(e) => e.stopPropagation()}>
        <h3 id="confirm-title">{title}</h3>
        <div className="muted">{message}</div>
        <div className="modal-actions">
          <button className="btn" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button ref={confirmRef} className={`btn ${cls}`} onClick={onConfirm} disabled={busy}>
            {busy ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
