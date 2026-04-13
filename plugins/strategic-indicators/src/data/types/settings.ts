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

export type AdminDepartmentItem = {
  department_id: string;
  department_name: string;
  short_name: string;
  strategic_summary: string;
  headline_goal: string;
  supporting_focus: string;
  weight_pct: number;
  aggregation_mode: "consolidated" | "average_of_units";
  is_active: boolean;
  display_order: number;
  created_at?: string;
  updated_at?: string;
  created_by_email?: string | null;
  updated_by_email?: string | null;
  indicators_count?: number;
};

export type AdminDepartmentsListResponse = {
  items: AdminDepartmentItem[];
};

export type CreateAdminDepartmentRequest = {
  department_id: string;
  department_name: string;
  short_name: string;
  strategic_summary?: string;
  headline_goal?: string;
  supporting_focus?: string;
  weight_pct?: number;
  aggregation_mode: "consolidated" | "average_of_units";
  display_order?: number;
};

export type UpdateAdminDepartmentRequest = {
  department_name: string;
  short_name: string;
  strategic_summary?: string;
  headline_goal?: string;
  supporting_focus?: string;
  weight_pct?: number;
  aggregation_mode: "consolidated" | "average_of_units";
  is_active?: boolean;
  display_order?: number;
};

export type PerformanceDirection =
  | "higher_is_better"
  | "lower_is_better";

export type AdminDepartmentIndicatorItem = {
  indicator_id: string;
  department_id: string;
  indicator_name: string;
  weight_pct: number;
  scope_type: "consolidated" | "per_unit";
  performance_direction: PerformanceDirection;
  strategic_description: string;
  source_key: string | null;
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
  scope_type: "consolidated" | "per_unit";
  performance_direction: PerformanceDirection;
  strategic_description?: string;
  source_key?: string | null;
  display_order?: number;
};

export type UpdateAdminDepartmentIndicatorRequest = {
  indicator_name: string;
  weight_pct: number;
  scope_type: "consolidated" | "per_unit";
  performance_direction: PerformanceDirection;
  strategic_description?: string;
  source_key?: string | null;
  is_active?: boolean;
  display_order?: number;
};