export type SettingsReadinessStatus = "ready" | "planned" | "mock";

export type SettingsReadinessItem = {
  id: string;
  title: string;
  status: SettingsReadinessStatus;
  description: string;
};

export type SettingsDashboardWeightItem = {
  id: string;
  departmentName: string;
  weightPct: number;
  note: string;
};

export type SettingsDashboardGoalItem = {
  id: string;
  departmentName: string;
  headlineGoal: string;
  supportingFocus: string;
};

export type SettingsDashboardParameterItem = {
  id: string;
  label: string;
  value: string;
  observation: string;
};

export type SettingsDashboardGovernanceItem = {
  id: string;
  label: string;
  value: string;
  observation: string;
};

export type SettingsDashboardMeta = {
  source: string;
  updatedAt: string | null;
  updatedByEmail: string | null;
};

export type SettingsDashboardData = {
  weights: SettingsDashboardWeightItem[];
  goals: SettingsDashboardGoalItem[];
  parameters: SettingsDashboardParameterItem[];
  governance: SettingsDashboardGovernanceItem[];
  readiness: SettingsReadinessItem[];
  meta: SettingsDashboardMeta;
};