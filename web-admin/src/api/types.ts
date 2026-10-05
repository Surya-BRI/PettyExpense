// Shapes returned by the FastAPI backend (services/transaction_service.transaction_to_dict,
// routes_auth._user_dict, routes_notifications, routes_admin /activity). Field names are
// kept exactly as the backend sends them (snake_case) so nothing is silently remapped.

export type Role = 'employee' | 'hod' | 'accountant' | 'finance_manager' | 'admin';
export type Stage = 'hod' | 'department_hod' | 'accountant' | 'finance_manager';
export type ClaimStatus = 'draft' | 'submitted' | 'disputed' | 'approved' | 'rejected' | 'paid';

export interface AuthUser {
  id: number;
  username?: string;
  display_name: string;
  role: Role;
  department_id?: number | null;
  /** Sent by newer backends only; older ones just have the id. */
  department_name?: string | null;
  email?: string | null;
  region_code?: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
}

export interface Receipt {
  id: number;
  s3_key: string;
  content_type?: string | null;
  ocr_vendor?: string | null;
  ocr_amount?: number | null;
  ocr_vat_amount?: number | null;
  ocr_total_amount?: number | null;
  ocr_currency?: string | null;
  ocr_date?: string | null;
  ocr_confidence?: number | null;
  image_hash?: string | null;
  /** Presigned S3 URL when available, otherwise the authenticated proxy path. */
  image_url: string;
  image_proxy_url: string;
}

export interface HistoryEntry {
  id: number;
  stage: string | null;
  actor_id: number;
  action: string;
  remarks: string | null;
  created_at: string | null;
}

export interface DuplicateWarning {
  reason: string;
  existing_claim_id?: number | null;
  message: string;
}

export interface ClaimLineItem {
  id: number;
  line_no: number;
  description: string;
  quantity: number | null;
  /** Line total as printed on the bill. */
  amount: number;
  category_id: number | null;
  category_name: string | null;
}

export interface Claim {
  id: number;
  type: 'reimbursement' | 'petty_cash' | string;
  employee_id: number;
  employee_name: string | null;
  region_id: number;
  region_code: string | null;
  project_id: number | null;
  category_id: number;
  category_name: string | null;
  vendor_id: number | null;
  vendor_name: string | null;
  vendor_unmatched: boolean;
  bill_date: string | null;
  currency: string;
  exchange_rate: number;
  amount: number;
  vat_amount: number;
  total_amount: number;
  op_number: string | null;
  status: ClaimStatus;
  current_stage: Stage | null;
  dispute_returned: boolean;
  remarks: string | null;
  duplicate_flag: boolean;
  ocr_confidence_json: string | null;
  created_at: string | null;
  updated_at: string | null;
  submitted_at: string | null;
  decided_at: string | null;
  paid_at: string | null;
  receipt: Receipt | null;
  duplicate_warning: DuplicateWarning | null;
  stage_sequence: string[];
  history?: HistoryEntry[];
  /** "multiple" for itemised bills (total = sum of line_items). Older backends omit both. */
  line_mode?: 'single' | 'multiple';
  line_items?: ClaimLineItem[];
}

export interface ActivityItem {
  id: number;
  transaction_id: number;
  stage: string | null;
  action: string;
  comment: string | null;
  actor_id: number;
  actor_name: string | null;
  employee_name: string | null;
  vendor_name: string | null;
  currency: string | null;
  total_amount: number | null;
  created_at: string | null;
}

export interface AppNotification {
  id: number;
  transaction_id: number | null;
  type: string;
  /** sent | read | failed */
  status: string;
  message: string | null;
  sent_at: string | null;
  current_stage: Stage | null;
  claim_status: ClaimStatus | null;
}

export interface VendorRef {
  id: number;
  name: string;
}
