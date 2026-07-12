export type NcDueSlaLevel = "none" | "ok" | "due_soon" | "overdue";

export type NcBoardSort =
  | "due_date_asc"
  | "due_date_desc"
  | "created_desc"
  | "priority_desc";

export type NcBoardFilterParams = {
  branch: string;
  date_start: string;
  date_end: string;
  area_id?: string;
  shift?: string;
  status?: string;
  priority?: string;
  responsible?: string;
  overdue_only?: boolean;
  senso_order?: number;
  search?: string;
  sort?: NcBoardSort;
  page: number;
  page_size: number;
};

export type NcBoardSummary = {
  nc_total: number;
  nc_open: number;
  nc_in_progress: number;
  nc_closed: number;
  nc_overdue: number;
  nc_pending?: number;
};

export type NcBoardItem = {
  id: string;
  audit_id: string;
  response_id: string;
  description: string | null;
  root_cause: string | null;
  corrective_action: string | null;
  responsible_name: string | null;
  due_date: string | null;
  priority: string | null;
  status: string;
  is_registered?: boolean;
  score?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
  audit_code: string;
  audit_date: string;
  area_name: string;
  branch_code: string;
  shift: string;
  criterion_code: string;
  criterion_description: string;
  senso_order: number;
  senso_name: string;
  plan_started: boolean;
  workflow_step: 1 | 2 | 3;
  due_sla_level: NcDueSlaLevel;
  days_until_due: number | null;
  has_before_evidence: boolean;
  has_after_evidence: boolean;
  last_action_at: string | null;
};

export type NcBoardPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type NcBoardData = {
  summary: NcBoardSummary;
  items: NcBoardItem[];
  pagination: NcBoardPagination;
};
