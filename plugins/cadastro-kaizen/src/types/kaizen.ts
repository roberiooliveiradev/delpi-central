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
  created_by_user_id: string;
  created_at: string;
};

export type KaizenEvidenceStage = "antes" | "depois" | "geral";
export type KaizenEvidenceType = "attachment" | "photo" | "document" | "link";

export type KaizenEvidence = {
  id: string;
  kaizen_id: string;
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
