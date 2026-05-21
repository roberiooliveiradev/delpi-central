export type SettingsWeightItem = {
  department_id: string;
  department_name: string;
  weight_pct: number;
};

export type SettingsGoalItem = {
  department_id: string;
  department_name: string;
  headline_goal: string;
  supporting_focus: string;
};

export type SettingsParameterItem = {
  key: string;
  label: string;
  value: string;
};

export type SettingsGovernanceItem = {
  key: string;
  label: string;
  value: string;
  observation: string;
};

export type StrategicIndicatorsSettingsResponse = {
  weights: {
    items: SettingsWeightItem[];
  };
  goals: {
    items: SettingsGoalItem[];
  };
  parameters: {
    items: SettingsParameterItem[];
  };
  governance: {
    items: SettingsGovernanceItem[];
  };
  meta: {
    source: string;
    updated_at: string | null;
    updated_by_email: string | null;
  };
};

export type StrategicIndicatorsSettingsUpdateRequest = {
  parameters: {
    items: SettingsParameterItem[];
  };
  governance: {
    items: SettingsGovernanceItem[];
  };
};

export type AggregationMode =
  | "consolidated"
  | "average_of_units";

export type ScopeType =
  | "consolidated"
  | "per_unit";

export type PerformanceDirection =
  | "higher_is_better"
  | "lower_is_better";

export type IndicatorValueUnit =
  | "percent"
  | "currency"
  | "ppm"
  | "days"
  | "hours"
  | "count"
  | "ratio"
  | "months"
  | string;

export type AdminDepartmentItem = {
  department_id: string;
  department_name: string;
  short_name: string;
  strategic_summary: string;
  headline_goal: string;
  supporting_focus: string;
  weight_pct: number;
  aggregation_mode: AggregationMode;
  is_active: boolean;
  display_order: number;
  created_at?: string;
  updated_at?: string;
  created_by_email?: string | null;
  updated_by_email?: string | null;
};

export type CreateAdminDepartmentRequest = {
  department_id: string;
  department_name: string;
  short_name: string;
  strategic_summary?: string;
  headline_goal?: string;
  supporting_focus?: string;
  weight_pct: number;
  aggregation_mode: AggregationMode;
  display_order?: number;
};

export type UpdateAdminDepartmentRequest = {
  new_department_id?: string;
  department_name: string;
  short_name: string;
  strategic_summary?: string;
  headline_goal?: string;
  supporting_focus?: string;
  weight_pct: number;
  aggregation_mode: AggregationMode;
  is_active?: boolean;
  display_order?: number;
};

export type AdminDepartmentsListResponse = {
  items: AdminDepartmentItem[];
};

export type AdminDepartmentIndicatorItem = {
  indicator_id: string;
  department_id: string;
  indicator_name: string;
  weight_pct: number;
  scope_type: ScopeType;
  performance_direction: PerformanceDirection;
  strategic_description: string;
  source_key: string | null;

  value_unit: IndicatorValueUnit | null;
  value_prefix: string | null;
  value_suffix: string | null;
  value_decimals: number;

  is_active: boolean;
  display_order: number;
  created_at?: string;
  updated_at?: string;
  created_by_email?: string | null;
  updated_by_email?: string | null;
};

export type AdminDepartmentIndicatorsListResponse = {
  items: AdminDepartmentIndicatorItem[];
};

export type CreateAdminDepartmentIndicatorRequest = {
  indicator_id: string;
  indicator_name: string;
  weight_pct: number;
  scope_type: ScopeType;
  performance_direction: PerformanceDirection;
  strategic_description?: string;
  source_key?: string | null;

  value_unit?: IndicatorValueUnit | null;
  value_prefix?: string | null;
  value_suffix?: string | null;
  value_decimals?: number;

  display_order?: number;
};

export type UpdateAdminDepartmentIndicatorRequest = {
  new_indicator_id?: string;
  indicator_name: string;
  weight_pct: number;
  scope_type: ScopeType;
  performance_direction: PerformanceDirection;
  strategic_description?: string;
  source_key?: string | null;

  value_unit?: IndicatorValueUnit | null;
  value_prefix?: string | null;
  value_suffix?: string | null;
  value_decimals?: number;

  is_active?: boolean;
  display_order?: number;
};