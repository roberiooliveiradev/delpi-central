import type { DepartmentOverviewViewItem } from "./departments";
import type { IndicatorViewItem } from "./indicators";

export type DepartmentTreeScopeKey = "consolidated" | "01" | "02";

export type DepartmentTreeScopeConfig = {
  key: DepartmentTreeScopeKey;
  branch?: string;
  label: string;
};

export type DepartmentTreeSparkPoint = {
  period: string;
  value: number;
};

export type DepartmentTreeIndicatorNode = {
  indicator: IndicatorViewItem;
  series: DepartmentTreeSparkPoint[];
};

export type DepartmentTreeDepartmentNode = {
  department: DepartmentOverviewViewItem;
  indicators: DepartmentTreeIndicatorNode[];
  series: DepartmentTreeSparkPoint[];
};

export type DepartmentTreeColumn = {
  scope: DepartmentTreeScopeConfig;
  departments: DepartmentTreeDepartmentNode[];
  averageScore: number | null;
  hasData: boolean;
};

export type DepartmentTreeMeasurementIssue = {
  departmentId: string;
  source: string;
  message: string;
  code?: string;
};

export type DepartmentTreeAlertSummary = {
  title: string;
  severity: string;
  impact: string;
  recommendation: string;
};

export type DepartmentTreeSnapshotVersions = {
  servingVersion: number;
  latestVersion: number;
  versionCount: number;
  servingFallbackFromPreviousClean: boolean;
  isClean: boolean;
};

export type DepartmentTreeDataQuality = {
  partialSuccess: boolean;
  errors: DepartmentTreeMeasurementIssue[];
  alertsSummary: DepartmentTreeAlertSummary[];
  snapshotVersions?: DepartmentTreeSnapshotVersions;
};

export type DepartmentTreeModel = {
  competence: string;
  igd: number | null;
  igdExact: number | null;
  classification: string | null;
  trendMonths?: number;
  igdSeries: DepartmentTreeSparkPoint[];
  columns: DepartmentTreeColumn[];
  departmentOrder: string[];
  dataQuality?: DepartmentTreeDataQuality;
};
