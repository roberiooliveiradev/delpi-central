export type GoalPeriodicity = "monthly" | "annual" | "quarterly" | "weekly";

export type StrategicIndicatorGoalItem = {
  id: string;
  indicator_id: string;
  goal_year: number;
  goal_label: string;
  goal_value: number;
  goal_periodicity: GoalPeriodicity;
  version: number;
  is_active: boolean;
  valid_from: string | null;
  valid_to: string | null;
  notes: string | null;
  created_by_user_id: string | null;
  created_by_email: string | null;
  updated_by_user_id: string | null;
  updated_by_email: string | null;
  created_at: string;
  updated_at: string;
};

export type StrategicIndicatorGoalListResponse = {
  items: StrategicIndicatorGoalItem[];
};

export type StrategicIndicatorGoalHistoryResponse = {
  items: StrategicIndicatorGoalItem[];
};

export type CreateStrategicIndicatorGoalRequest = {
  indicator_id: string;
  goal_year: number;
  goal_label: string;
  goal_value: number;
  goal_periodicity: GoalPeriodicity;
  valid_from?: string | null;
  valid_to?: string | null;
  notes?: string | null;
};

export type UpdateStrategicIndicatorGoalRequest = {
  goal_label: string;
  goal_value: number;
  goal_periodicity: GoalPeriodicity;
  valid_from?: string | null;
  valid_to?: string | null;
  notes?: string | null;
};

export type BulkCreateStrategicIndicatorGoalItemRequest = {
  indicator_id: string;
  goal_label: string;
  goal_value: number;
  goal_periodicity: GoalPeriodicity;
  valid_from?: string | null;
  valid_to?: string | null;
  notes?: string | null;
};

export type BulkCreateStrategicIndicatorGoalsRequest = {
  goal_year: number;
  items: BulkCreateStrategicIndicatorGoalItemRequest[];
};

export type DuplicateStrategicIndicatorGoalsYearRequest = {
  source_year: number;
  target_year: number;
  department_ids?: string[];
  overwrite_existing?: boolean;
};

export type FillMissingStrategicIndicatorGoalsRequest = {
  goal_year: number;
  department_ids?: string[];
  copy_from_year?: number | null;
};

export type GoalYearOverviewItem = {
  goal_year: number;
  total_versions: number;
  total_active_versions: number;
  total_active_indicators: number;
};

export type GoalYearsOverviewResponse = {
  items: GoalYearOverviewItem[];
};

export type BulkGoalMutationResponse = {
  message: string;
  items: StrategicIndicatorGoalItem[];
};