export type StrategicIndicatorGoalItem = {
  id: string;
  indicator_id: string;
  goal_year: number;
  goal_label: string;
  goal_value: number;
  goal_periodicity: "monthly" | "annual" | "quarterly" | "weekly";
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
  goal_periodicity: "monthly" | "annual" | "quarterly" | "weekly";
  valid_from?: string | null;
  valid_to?: string | null;
  notes?: string | null;
};

export type UpdateStrategicIndicatorGoalRequest = {
  goal_label: string;
  goal_value: number;
  goal_periodicity: "monthly" | "annual" | "quarterly" | "weekly";
  valid_from?: string | null;
  valid_to?: string | null;
  notes?: string | null;
};