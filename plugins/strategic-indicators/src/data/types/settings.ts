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
};