import type { StrategicIndicatorsDepartmentsResponse } from "./departments";
import type { StrategicIndicatorsResponse } from "./indicators";
import type { StrategicIndicatorsTrendsResponse } from "./trends";
import type { DepartmentTreeScopeKey } from "./departmentTree";

export type StrategicIndicatorsDepartmentTreeScopeApi = {
  scope_key: DepartmentTreeScopeKey;
  scope_label: string;
  branch?: string | null;
  departments: StrategicIndicatorsDepartmentsResponse & {
    partial_success?: boolean;
    errors?: unknown[];
  };
  indicators: StrategicIndicatorsResponse & {
    partial_success?: boolean;
    errors?: unknown[];
  };
  trends: StrategicIndicatorsTrendsResponse;
};

export type StrategicIndicatorsDepartmentTreeResponse = {
  competence: string;
  igd: number | null;
  igd_exact: number | null;
  classification: string | null;
  months: number;
  scopes: StrategicIndicatorsDepartmentTreeScopeApi[];
  meta?: {
    source?: string;
    scope_count?: number;
  };
};

export type StrategicIndicatorsTreeSnapshotScopeApi = {
  scope_key: DepartmentTreeScopeKey;
  scope_label: string;
  branch?: string | null;
  departments: StrategicIndicatorsDepartmentsResponse & {
    partial_success?: boolean;
    errors?: unknown[];
  };
  indicators: StrategicIndicatorsResponse & {
    partial_success?: boolean;
    errors?: unknown[];
  };
};

export type StrategicIndicatorsMeasurementIssueApi = {
  department_id?: string;
  source?: string;
  message?: string;
  code?: string;
};

export type StrategicIndicatorsAlertSummaryApi = {
  title: string;
  severity: string;
  impact: string;
  recommendation: string;
};

export type MeasurementVersionsMetaApi = {
  serving_version: number;
  latest_version: number;
  version_count: number;
  serving_fallback_from_previous_clean: boolean;
  is_clean: boolean;
};

export type StrategicIndicatorsTreeSnapshotResponse = {
  competence: string;
  igd: number | null;
  igd_exact: number | null;
  classification: string | null;
  errors?: StrategicIndicatorsMeasurementIssueApi[];
  partial_success?: boolean;
  alerts_summary?: StrategicIndicatorsAlertSummaryApi[];
  scopes: StrategicIndicatorsTreeSnapshotScopeApi[];
  meta?: {
    source?: string;
    scope_count?: number;
    measurement_versions?: MeasurementVersionsMetaApi | null;
  };
};

export type StrategicIndicatorsTreeTrendsScopeApi = {
  scope_key: DepartmentTreeScopeKey;
  scope_label: string;
  branch?: string | null;
  trends: StrategicIndicatorsTrendsResponse;
};

export type StrategicIndicatorsTreeTrendsResponse = {
  competence: string;
  months: number;
  scopes: StrategicIndicatorsTreeTrendsScopeApi[];
  meta?: { source?: string; scope_count?: number };
};

export type StrategicIndicatorsTreeLoadJobCreateResponse = {
  job_id: string;
  state: "queued" | "running" | "succeeded" | "failed";
  phase: "snapshot" | "trends" | "done" | "error";
  progress_pct: number;
  message: string;
  created_at: string;
  updated_at: string;
};

export type StrategicIndicatorsTreeLoadJobStatusResponse = StrategicIndicatorsTreeLoadJobCreateResponse & {
  snapshot?: StrategicIndicatorsTreeSnapshotResponse | null;
  trends?: StrategicIndicatorsTreeTrendsResponse | null;
  error?: string | null;
};
