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

export type DepartmentTreeModel = {
  competence: string;
  igd: number | null;
  igdExact: number | null;
  classification: string | null;
  igdSeries: DepartmentTreeSparkPoint[];
  columns: DepartmentTreeColumn[];
  departmentOrder: string[];
};
