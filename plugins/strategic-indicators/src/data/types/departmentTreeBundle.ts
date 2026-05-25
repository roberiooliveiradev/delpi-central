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

export type StrategicIndicatorsTreeSnapshotResponse = {
  competence: string;
  igd: number | null;
  igd_exact: number | null;
  classification: string | null;
  scopes: StrategicIndicatorsTreeSnapshotScopeApi[];
  meta?: { source?: string; scope_count?: number };
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
