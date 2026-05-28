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

export type AdminConfigImportResponse = {
  message: string;
  stats: {
    departments_upserted: number;
    indicators_upserted: number;
    goals_created: number;
    goals_skipped: number;
    module_settings_updated: number;
  };
};
