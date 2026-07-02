export type SavingsType = "tempo" | "material" | "financeiro" | "qualitativo" | "misto";

export type KaizenStatus = "em_andamento" | "implantado" | "descontinuado" | "cancelado";

export type ParticipantRole = "responsavel" | "participante" | "apoio";

export type KaizenParticipant = {
  id?: string;
  name: string;
  role: ParticipantRole;
  user_id?: string | null;
};

export type KaizenRecord = {
  id: string;
  branch_code: string;
  title: string;
  accountable: string | null;
  sector: string | null;
  investment: number | null;
  savings_type: SavingsType;
  seconds_per_occurrence: number | null;
  occurrences_per_day: number | null;
  hourly_cost: number | null;
  quantity_saved_per_day: number | null;
  unit_material_cost: number | null;
  fixed_daily_savings: number | null;
  daily_savings: number | null;
  annual_savings: number | null;
  realized_daily_savings: number | null;
  realized_annual_savings: number | null;
  status: KaizenStatus;
  date_implemented: string | null;
  date_discontinued: string | null;
  notes: string | null;
  process_description: string | null;
  problem_description: string | null;
  improvement_description: string | null;
  expected_result: string | null;
  category: string | null;
  current_revision_number: number | null;
  savings_valid_until: string | null;
  savings_active: boolean;
  participants?: KaizenParticipant[];
  created_at: string;
  updated_at: string;
};

export type KaizenListResponse = {
  items: KaizenRecord[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};

export type KaizenRevisionChangeType =
  | "baseline"
  | "implantacao"
  | "melhoria"
  | "correcao"
  | "descontinuacao"
  | "restauracao";

// Ciclo de vida de uma VERSÃO do kaizen (revisão = versão completa do processo).
export type KaizenVersionStatus =
  | "em_andamento"
  | "implantado"
  | "descontinuado"
  | "cancelado"
  | "substituido";

export type KaizenRevision = {
  id: string;
  kaizen_id: string;
  revision_number: number;
  change_type: KaizenRevisionChangeType;
  change_summary: string | null;
  change_reason: string | null;
  effective_from: string;
  effective_until: string | null;
  snapshot: Record<string, unknown>;
  snapshot_schema_version: number;
  daily_savings: number | null;
  annual_savings: number | null;
  version_status: KaizenVersionStatus | null;
  savings_valid_until: string | null;
  created_by_user_id: string;
  created_by_name: string | null;
  created_at: string;
};

export type KaizenHistoryEvent = {
  id: string;
  kaizen_id: string;
  event_type: string;
  old_value: string | null;
  new_value: string | null;
  comment: string | null;
  created_by_user_id: string;
  created_by_name: string | null;
  created_at: string;
};

export type KaizenAuditEntry = {
  id: string;
  kaizen_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  actor_user_id: string;
  actor_name: string | null;
  created_at: string;
};

export type KaizenSavingsTimelineImprovement = KaizenRevision;

export type KaizenSavingsTimeline = {
  kaizen_id: string;
  date_start: string | null;
  date_end: string | null;
  period_savings: number;
  current: {
    revision_number: number | null;
    daily_savings: number | null;
    annual_savings: number | null;
    valid_until: string | null;
    active: boolean;
  };
  improvements: KaizenSavingsTimelineImprovement[];
};

export type KaizenSummaryBucket = { key: string; value: number };

export type KaizenSummaryExpiring = {
  id: string;
  title: string;
  branch_code: string;
  valid_until: string;
  days_left: number;
};

export type KaizenSummaryRecent = {
  id: string;
  title: string;
  branch_code: string;
  status: KaizenStatus;
  date_implemented: string | null;
  updated_at: string | null;
};

export type KaizenSummary = {
  filters: { branch_code: string | null; date_start: string | null; date_end: string | null };
  has_period: boolean;
  total: number;
  implantados: number;
  em_andamento: number;
  descontinuados: number;
  cancelados: number;
  period_savings: number;
  period_implanted_count: number;
  active_annual_savings: number;
  realized_annual_savings: number;
  active_count: number;
  total_investment: number;
  expired_but_implanted: number;
  by_status: KaizenSummaryBucket[];
  by_branch: KaizenSummaryBucket[];
  by_savings_type: KaizenSummaryBucket[];
  by_category: KaizenSummaryBucket[];
  top_accountables: KaizenSummaryBucket[];
  implanted_by_month: KaizenSummaryBucket[];
  expiring_soon: KaizenSummaryExpiring[];
  recent: KaizenSummaryRecent[];
};

export type KaizenEvidenceStage = "antes" | "depois" | "geral";
export type KaizenEvidenceType = "attachment" | "photo" | "document" | "link";

export type KaizenEvidence = {
  id: string;
  kaizen_id: string;
  revision_id: string | null;
  type: KaizenEvidenceType;
  stage: KaizenEvidenceStage;
  file_name: string | null;
  stored_name: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  description: string | null;
  external_url: string | null;
  uploaded_by_user_id: string;
  uploaded_by_name: string | null;
  created_at: string;
};

export type KaizenFormValues = {
  branch_code: string;
  title: string;
  sector: string;
  category: string;
  investment: string;
  savings_type: SavingsType | "";
  seconds_per_occurrence: string;
  occurrences_per_day: string;
  hourly_cost: string;
  quantity_saved_per_day: string;
  unit_material_cost: string;
  fixed_daily_savings: string;
  realized_daily_savings: string;
  status: KaizenStatus;
  date_implemented: string;
  date_discontinued: string;
  notes: string;
  process_description: string;
  problem_description: string;
  improvement_description: string;
  expected_result: string;
  participants: KaizenParticipant[];
};
