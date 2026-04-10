export type StrategicIndicatorsAuditEntityKey =
  | "departments"
  | "department_indicators"
  | "indicator_goals"
  | "parameters.global"
  | "governance.notes"
  | "weights.departments"
  | "goals.summary";

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

export type StrategicIndicatorsChangeRequest = {
  id: string;
  request_code: string;
  title: string;
  description: string;
  target_block: string;
  proposed_payload: Record<string, unknown>;
  status: "draft" | "submitted" | "approved" | "rejected" | "cancelled";
  created_by_user_id: string | null;
  created_by_email: string | null;
  submitted_by_user_id: string | null;
  submitted_by_email: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type StrategicIndicatorsChangeRequestListResponse = {
  items: StrategicIndicatorsChangeRequest[];
};