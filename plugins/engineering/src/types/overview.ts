/** Contrato versionado da Visão geral — espelho de
 * `engineering-api/engineering_app/application/models/overview.py`
 * (schema 1.0). O MFE consome o envelope canônico da BFF; nunca
 * envelopes internos dos owners (api-delpi/Strategic Indicators). */

export type IndicatorAvailability =
  | "available"
  | "empty"
  | "unavailable"
  | "forbidden";

export type OverviewStatus = "available" | "partial" | "unavailable";

export type IndicatorFamily = "lmp" | "transforma";

export type OverviewFilters = {
  start_date?: string | null;
  end_date?: string | null;
  competence?: string | null;
  branch?: string | null;
};

export type OverviewIndicator = {
  id: string;
  label: string;
  family: IndicatorFamily;
  availability: IndicatorAvailability;
  value?: number | null;
  unit?: string | null;
  scope?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  source: string;
  source_endpoint?: string | null;
  // Campos de meta/IDD repassados dos owners — só presentes quando o
  // owner os fornece (nunca recalculados no MFE).
  has_goal?: boolean | null;
  goal_label?: string | null;
  goal_value?: number | null;
  comparable_goal?: number | null;
  reference_goal?: number | null;
  target?: number | null;
  goal_aggregation?: string | null;
  goal_mode?: string | null;
  goal_period_kind?: string | null;
  goal_scope_branch?: string | null;
  goal_scope_label?: string | null;
  goal_scope_hint?: string | null;
  scope_type?: string | null;
  goal_period_partial?: boolean | null;
  performance_direction?: string | null;
  value_unit?: string | null;
  value_prefix?: string | null;
  value_suffix?: string | null;
  value_decimals?: number | null;
  idd?: number | null;
  idd_label?: string | null;
  reason?: string | null;
  message?: string | null;
};

export type OverviewResponse = {
  schema_version: string;
  generated_at: string;
  filters: OverviewFilters;
  status: OverviewStatus;
  indicators: OverviewIndicator[];
};

export type OverviewEnvelope = {
  success: boolean;
  message?: string | null;
  data: OverviewResponse;
  meta?: Record<string, unknown>;
};
