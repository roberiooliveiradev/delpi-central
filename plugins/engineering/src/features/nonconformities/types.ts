/** Tipos do bounded context de Não Conformidades — espelho dos
 * contratos E-NC-* da Engineering API (doc 47). */

export type NcStatus = "open" | "in_progress" | "done";

export type NcProduct = {
  product_code: string;
  product_description: string | null;
};

export type Nonconformity = {
  id: string;
  registered_at: string | null;
  occurrence_date: string | null;
  sale_number: string | null;
  lmp_number: string | null;
  customer_name: string | null;
  launch_date: string | null;
  last_revision_date: string | null;
  executed_by: string | null;
  released_by: string | null;
  status: NcStatus;
  defect_description: string | null;
  corrective_actions: string | null;
  technical_opinion: string | null;
  problem_tags: string[];
  products: NcProduct[];
  product_codes: string[];
  created_by: string | null;
  updated_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type NcListResult = {
  items: Nonconformity[];
  total: number;
  page: number;
  page_size: number;
  sort_by: string;
  sort_dir: string;
};

export type NcHistoryField = {
  field: string;
  label: string;
  old: unknown;
  new: unknown;
};

export type NcHistoryEvent = {
  id: string;
  nonconformity_id: string;
  event_type: "created" | "updated";
  changes: { fields?: NcHistoryField[] };
  actor_user_id: string;
  actor_email: string | null;
  actor_name: string | null;
  created_at: string | null;
};

export type NcProblemTag = {
  id: string;
  label: string;
  usage_count: number;
};

export type NcIndicators = {
  current_days_without_nc: number;
  record_days_without_nc: number;
  last_nc_date: string | null;
  reference_start_date: string | null;
  reference_start_degraded?: boolean;
  as_of_date: string;
  nc_count: number;
};

export type NcContextPayload = {
  nonconformity: Nonconformity;
  ov_status: string;
  ov: Record<string, unknown> | null;
  product_contexts: {
    product_code: string;
    product_description: string | null;
    structure_status: string;
    structure: unknown;
  }[];
  product_contexts_truncated: boolean;
};

export type NcPayload = {
  status?: NcStatus;
  sale_number?: string | null;
  lmp_number?: string | null;
  customer_name?: string | null;
  occurrence_date?: string | null;
  launch_date?: string | null;
  last_revision_date?: string | null;
  executed_by?: string | null;
  released_by?: string | null;
  defect_description?: string | null;
  corrective_actions?: string | null;
  technical_opinion?: string | null;
  problem_tags?: string[];
  products?: NcProduct[];
  expected_updated_at?: string | null;
};

export type NcImportReport = {
  deleted: number;
  created: number;
  skipped: number;
  errors: number;
  items: {
    index: number;
    result: string;
    reason?: string;
    sale_number?: string | null;
    record_id?: string;
  }[];
};
