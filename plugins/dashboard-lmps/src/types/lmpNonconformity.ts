export type LmpNcStatus = "open" | "in_progress" | "done";

export type LmpNcProductLine = {
  product_code: string;
  product_description?: string | null;
};

export type LmpNonconformity = {
  id: string;
  registered_at: string;
  sale_number?: string | null;
  lmp_number?: string | null;
  customer_name?: string | null;
  launch_date?: string | null;
  last_revision_date?: string | null;
  executed_by?: string | null;
  released_by?: string | null;
  status: LmpNcStatus | string;
  defect_description?: string | null;
  problem_tags?: string[];
  corrective_actions?: string | null;
  technical_opinion?: string | null;
  products?: LmpNcProductLine[];
  product_codes?: string[];
  created_by?: string | null;
  updated_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type LmpNonconformityListResponse = {
  items: LmpNonconformity[];
  total: number;
  page: number;
  page_size: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc" | string;
};

/** Placar: dias atuais e recorde sem NC em LMPs. */
export type LmpNonconformityStreak = {
  current_days_without_nc: number;
  record_days_without_nc: number;
  last_nc_date: string | null;
  /** Âncora (primeira OV) quando não há NC cadastrada. */
  reference_start_date?: string | null;
  as_of_date: string;
  nc_count: number;
};

export type LmpProblemTag = {
  id: string;
  label: string;
  usage_count: number;
};

export type LmpProblemTagListResponse = {
  items: LmpProblemTag[];
  total: number;
};

export type LmpNonconformityPayload = {
  status: LmpNcStatus;
  sale_number?: string | null;
  lmp_number?: string | null;
  customer_name?: string | null;
  launch_date?: string | null;
  last_revision_date?: string | null;
  executed_by?: string | null;
  released_by?: string | null;
  defect_description?: string | null;
  problem_tags?: string[];
  corrective_actions?: string | null;
  technical_opinion?: string | null;
  products?: LmpNcProductLine[];
};

export type LmpNcHistoryChangeField = {
  field: string;
  label: string;
  old: unknown;
  new: unknown;
};

export type LmpNcHistoryEvent = {
  id: string;
  nonconformity_id: string;
  event_type: "created" | "updated" | string;
  changes: { fields?: LmpNcHistoryChangeField[] };
  actor_user_id: string;
  actor_email?: string | null;
  actor_name?: string | null;
  created_at: string;
};

export type LmpNcHistoryListResponse = {
  items: LmpNcHistoryEvent[];
  total: number;
};

export type LmpNonconformityExportFile = {
  version: number;
  generated_at?: string;
  count: number;
  items: LmpNonconformity[];
};

export type ImportLmpNonconformitiesResult = {
  created: number;
  skipped: number;
  errors: number;
  items: Array<Record<string, unknown>>;
};

export const LMP_NC_STATUS_OPTIONS: { value: LmpNcStatus; label: string }[] = [
  { value: "open", label: "Aberta" },
  { value: "in_progress", label: "Em andamento" },
  { value: "done", label: "Concluída" },
];

export function lmpNcStatusLabel(status: string): string {
  return LMP_NC_STATUS_OPTIONS.find((o) => o.value === status)?.label ?? status;
}
