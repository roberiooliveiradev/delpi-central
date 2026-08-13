import type { DashboardGoalFields } from "@delpi/plugin-ui/index";

export type AnalyticsCustomerSegment = "weg" | "new_business";

export type AnalyticsFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
  customer_segment?: AnalyticsCustomerSegment;
  /** Filtro de carteira — commercial-api resolve customer_codes no servidor. CSV multi. */
  seller_id?: string;
  /**
   * Conta 360: filtra OVs deste código sem membership de carteira
   * (`account_customer_code` no BFF).
   */
  account_customer_code?: string;
  status?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  search?: string;
};

export type RolTargetData = DashboardGoalFields & {
  branch?: string | null;
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
  /** Meta % do período (quando a API envia). */
  target?: number | null;
  comparable_goal?: number | null;
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

export type CommercialProposalStatusCategory = "won" | "lost" | "open" | "other";

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

export type CommercialProduct = {
  code: string;
  description?: string | null;
  group_code?: string | null;
  type?: string | null;
  qtd_pi?: number | null;
};

export type CommercialProposalHistoryEvent = {
  revision: string;
  process_code: string;
  stage_code: string;
  process_label?: string | null;
  stage_label?: string | null;
  start_date?: string | null;
  start_time?: string | null;
  end_date?: string | null;
  end_time?: string | null;
  duration_display?: string | null;
  duration_minutes?: number | null;
  status?: string | null;
  status_label?: string | null;
  is_open?: boolean;
  is_late?: boolean;
  is_current?: boolean;
  is_engineering?: boolean;
  is_engineering_flow?: boolean;
  is_engineering_entry?: boolean;
  flow_transition?: string | null;
  flow_transition_label?: string | null;
  flow_transition_labels?: string[] | null;
};

export type CommercialProposalDetail = CommercialProposal & {
  customer_name?: string | null;
  customer_store?: string | null;
  seller_code?: string | null;
  seller_name?: string | null;
  process_code?: string | null;
  process_label?: string | null;
  stage_label?: string | null;
  list_history?: CommercialProposalHistoryEvent[];
  list_products?: CommercialProduct[];
};

export type CommercialProposalHistoryEventsData = {
  items: CommercialProposalHistoryEvent[];
  total?: number;
  reference_revision?: string | null;
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
  start_date: string;
  end_date: string;
  rol_matrix: number;
  rol_branch: number;
};

export type CommercialRolSeriesData = {
  granularity: string;
  truncated: boolean;
  points: CommercialRolSeriesPoint[];
};

export type SalesOrderOtdLineStatus = "on_time" | "late";

export type SalesOrderOtdLineItem = {
  branch: string;
  order_number: string;
  line_item: string;
  product_code?: string | null;
  product_description?: string | null;
  customer_code?: string | null;
  customer_name?: string | null;
  qty_sold?: number | null;
  qty_delivered?: number | null;
  promised_date?: string | null;
  invoice_date?: string | null;
  is_invoiced?: number | null;
  status: SalesOrderOtdLineStatus;
  days_diff?: number | null;
};

export type SalesOrderOtdPanelData = {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  summary: {
    total_lines: number;
    on_time_lines: number;
    late_lines: number;
    sales_order_otd_pct: number | null;
  };
  lines: {
    items: SalesOrderOtdLineItem[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};

export type SalesOrderOtdSeriesPoint = {
  periodo: string;
  sort_key: string;
  start_date: string;
  end_date: string;
  otd_filial_01: number | null;
  otd_filial_02: number | null;
};

export type SalesOrderOtdSeriesData = {
  granularity: string;
  truncated: boolean;
  points: SalesOrderOtdSeriesPoint[];
};

export type SalesOrderOtdLineDetailData = {
  branch: string;
  order_number: string;
  line_item: string;
  line: SalesOrderOtdLineItem;
};

export type ChartGranularity = "day" | "week" | "month" | "year";
