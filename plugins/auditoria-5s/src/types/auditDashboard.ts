export type ChartGranularity = "day" | "week" | "month";

export type AuditDashboardFilterParams = {
  branch: string;
  start_date: string;
  end_date: string;
  area_id?: string;
  shift?: string;
  audit_status?: string;
  senso_order?: number;
  granularity: ChartGranularity;
  page: number;
  page_size: number;
};

export type AuditDashboardSummary = {
  audit_count: number;
  average_score_pct: number | null;
  nc_total: number;
  nc_open: number;
  nc_closed: number;
  nc_overdue: number;
  filtered_senso_order?: number | null;
  filtered_senso_name?: string | null;
};

export type ScoreByPeriodPoint = {
  period: string;
  average_score_pct: number | null;
  audit_count: number;
};

export type ScoreByAreaPoint = {
  area_id: string;
  area_name: string;
  average_score_pct: number | null;
  audit_count: number;
};

export type ScoreBySensoPoint = {
  senso_order: number;
  senso_name: string;
  average_score_pct: number | null;
};

export type NcByStatusPoint = {
  status: string;
  count: number;
};

export type AuditDashboardCharts = {
  score_by_period: ScoreByPeriodPoint[];
  score_by_area: ScoreByAreaPoint[];
  score_by_senso: ScoreBySensoPoint[];
  nc_by_status: NcByStatusPoint[];
};

export type AuditDashboardItem = {
  id: string;
  audit_code: string;
  audit_date: string;
  area_name: string;
  shift: string;
  status: string;
  overall_score_pct: number | null;
  senso_score_pct?: number | null;
  auditor_names?: string | null;
  nc_total: number;
  nc_open: number;
};

export type AuditDashboardPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type AuditDashboardData = {
  summary: AuditDashboardSummary;
  charts: AuditDashboardCharts;
  items: AuditDashboardItem[];
  pagination: AuditDashboardPagination;
};
