import type { DashboardGoalFields } from "../utils/goalDisplay";

export type RolTargetData = DashboardGoalFields & {
  branch: string;
  start_date?: string | null;
  end_date?: string | null;
  rol: number;
  target: number | null;
  rol_target_pct: number | null;
};

export type ClosingRateData = DashboardGoalFields & {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  qtd_proposals: number;
  qtd_won: number;
  sales_conversion_rate_pct: number | null;
};

export type NewClientsAverageData = {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  total_new_clients: number;
  qtd_months: number;
  monthly_average: number;
};

export type NewClientsRolPctData = {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  new_clients_rol_pct: number | null;
};

export type SalesOrderOtdData = DashboardGoalFields & {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  total_lines: number;
  on_time_lines: number;
  late_lines: number;
  sales_order_otd_pct: number | null;
};

export type NewBusinessRolPctData = DashboardGoalFields & {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  total_rol: number;
  new_business_rol: number;
  weg_rol: number;
  new_business_rol_pct: number | null;
};

export type CommercialCustomerSegment = "weg" | "new_business";

export type CommercialFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
  customer_segment?: CommercialCustomerSegment;
  status?: string;
  page?: number;
  page_size?: number;
};

export type CommercialProposalStatusCategory =
  | "won"
  | "lost"
  | "open"
  | "other";

export type CommercialProposalStatusFilter = "all" | "won" | "open";

export type CommercialProposal = {
  branch: string;
  proposal_number: string;
  revision: string;
  description?: string | null;
  proposal_date?: string | null;
  end_date?: string | null;
  status_code?: string | null;
  status_label?: string | null;
  status_category?: CommercialProposalStatusCategory | null;
  customer_code?: string | null;
  customer_store?: string | null;
  stage?: string | null;
};

export type CommercialProposalDetail = CommercialProposal & {
  customer_name?: string | null;
  seller_code?: string | null;
  seller_name?: string | null;
  process_code?: string | null;
  process_label?: string | null;
  stage_label?: string | null;
};

export type CommercialProposalHistoryEvent = {
  revision: string;
  process_code: string;
  stage_code: string;
  process_label?: string | null;
  stage_label?: string | null;
  start_date?: string | null;
  start_time?: string | null;
  limit_date?: string | null;
  limit_time?: string | null;
  end_date?: string | null;
  end_time?: string | null;
  duration_minutes?: number | null;
  duration_display?: string | null;
  status?: string | null;
  status_label?: string | null;
  history_flag?: string | null;
  is_engineering?: boolean;
  is_engineering_flow?: boolean;
  is_open?: boolean;
  is_late?: boolean;
  is_current?: boolean;
  is_engineering_entry?: boolean;
  flow_transition?: string | null;
  flow_transition_label?: string | null;
  flow_transitions?: string[];
  flow_transition_labels?: string[];
};

export type CommercialProposalDetailData = CommercialProposalDetail & {
  list_history?: CommercialProposalHistoryEvent[];
};

export type CommercialProposalsPage = {
  items: CommercialProposal[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type CommercialRolSeriesPoint = {
  periodo: string;
  sort_key: string;
  date_start: string;
  date_end: string;
  rol_matrix: number;
  rol_branch: number;
};

export type CommercialRolSeriesData = {
  granularity: string;
  truncated: boolean;
  points: CommercialRolSeriesPoint[];
};
