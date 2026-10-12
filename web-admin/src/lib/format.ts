import type { AuthUser, Claim, ClaimStatus, Role, Stage } from '../api/types';

const moneyFmt = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const compactFmt = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 });

/** "1 claim", "3 claims". */
export const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`;

/** Currency code prefix + grouped digits, same as the mobile app ("AED 1,234.50"). */
export const money = (currency: string, value: number) => `${currency} ${moneyFmt.format(value)}`;
export const compact = (value: number) => compactFmt.format(value);

/** Backend timestamps are naive UTC (`datetime.utcnow().isoformat()`, no "Z"). */
export function parseUtc(raw: string | null | undefined): Date | null {
  if (!raw) return null;
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(raw) ? raw : `${raw}Z`);
  return Number.isNaN(d.getTime()) ? null : d;
}

const dubaiDate = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Dubai', day: 'numeric', month: 'short', year: 'numeric' });
const dubaiDateTime = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Dubai',
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
});

/** UAE has no daylight saving, so Asia/Dubai is exact year-round. */
export const formatDate = (raw: string | null | undefined) => {
  const d = parseUtc(raw);
  return d ? dubaiDate.format(d) : '-';
};
export const formatDateTime = (raw: string | null | undefined) => {
  const d = parseUtc(raw);
  return d ? dubaiDateTime.format(d) : '-';
};

export function timeAgo(raw: string | null | undefined): string {
  const d = parseUtc(raw);
  if (!d) return '';
  const mins = Math.round((Date.now() - d.getTime()) / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days} d ago`;
  return formatDate(raw);
}

export const STATUS_LABELS: Record<ClaimStatus, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  disputed: 'Disputed',
  approved: 'Approved',
  rejected: 'Rejected',
  paid: 'Paid',
};

export const STAGE_LABELS: Record<string, string> = {
  employee: 'Employee',
  hod: 'HOD',
  department_hod: 'Department HOD',
  accountant: 'Accountant',
  finance_manager: 'Finance Manager',
};

export const ROLE_LABELS: Record<Role, string> = {
  employee: 'Employee',
  hod: 'Head of Department',
  accountant: 'Accountant',
  finance_manager: 'Finance Manager',
  admin: 'Admin',
};

export const ACTION_LABELS: Record<string, string> = {
  approve: 'approved',
  dispute: 'disputed',
  reject: 'rejected',
  submitted: 'submitted',
  created: 'saved a draft of',
  edited: 'edited',
  paid: 'marked paid',
  vendor_resolved: 'resolved the vendor on',
};

export const PENDING: ClaimStatus[] = ['submitted', 'disputed'];

export const isApprover = (user: AuthUser) => user.role !== 'employee';

/** The approval queue(s) a role works from. An HOD covers both HOD stages. */
export function stagesFor(role: Role): Stage[] {
  switch (role) {
    case 'hod':
      return ['hod', 'department_hod'];
    case 'accountant':
      return ['accountant'];
    case 'finance_manager':
      return ['finance_manager'];
    case 'admin':
      return ['hod', 'department_hod', 'accountant', 'finance_manager'];
    default:
      return [];
  }
}

export const claimTotal = (c: Claim) => c.total_amount ?? c.amount + c.vat_amount;
export const claimWhen = (c: Claim) => parseUtc(c.submitted_at ?? c.created_at);
export const vendorOf = (c: Claim) => c.vendor_name || `Claim #${c.id}`;
