export type AdminConfigImportMode = "merge" | "replace";

export type AdminConfigBundle = {
  schema_version: number;
  exported_at?: string;
  departments: Array<Record<string, unknown>>;
  department_indicators: Array<Record<string, unknown>>;
  indicator_goals: Array<Record<string, unknown>>;
  module_settings: {
    parameters?: Record<string, unknown>;
    governance?: Record<string, unknown>;
  };
};

export type AdminConfigPlannedCounts = {
  in_file: number;
  insert: number;
  update: number;
  skip: number;
  delete: number;
};

export type AdminConfigPreviewResponse = {
  valid: boolean;
  errors: string[];
  mode: AdminConfigImportMode;
  current_counts: {
    departments: number;
    department_indicators: number;
    indicator_goals: number;
  };
  planned: {
    departments: AdminConfigPlannedCounts;
    department_indicators: AdminConfigPlannedCounts;
    indicator_goals: AdminConfigPlannedCounts;
    module_settings: AdminConfigPlannedCounts;
  };
};

export type AdminConfigImportResponse = {
  message: string;
  stats: {
    mode: AdminConfigImportMode;
    departments_upserted: number;
    indicators_upserted: number;
    goals_created: number;
    goals_skipped: number;
    goals_deleted: number;
    departments_deleted: number;
    indicators_deleted: number;
    module_settings_updated: number;
  };
};
