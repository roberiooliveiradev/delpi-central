export type HrFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
};

export type HrBranchMetrics = {
  branch_code: string;
  absenteeism_pct: number | null;
  turnover_pct: number | null;
  training_hours_per_collaborator: number | null;
  active_pdi_pct: number | null;
};

export type HrSnapshot = {
  start_date: string | null;
  end_date: string | null;
  internal_satisfaction_pct: number | null;
  active_pdi_pct: number | null;
  branches: HrBranchMetrics[];
};

export type HrBranchesResponse = {
  branches: string[];
};
