export type StrategicIndicatorsAuditEntityKey =
  | "weights.departments"
  | "goals.summary"
  | "parameters.global"
  | "governance.notes";

export type StrategicIndicatorsSettingsAuditItem = {
  id: string;
  event_type: string;
  entity_key: string;
  payload_before: Record<string, unknown> | null;
  payload_after: Record<string, unknown> | null;
  changed_by_user_id: string | null;
  changed_by_email: string | null;
  created_at: string;
};

export type StrategicIndicatorsSettingsAuditResponse = {
  items: StrategicIndicatorsSettingsAuditItem[];
};