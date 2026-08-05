export type ExerciseStatus = "draft" | "open" | "closing" | "locked" | "archived";

export type BudgetExercise = {
  id: string;
  year: number;
  name: string;
  description?: string | null;
  status: ExerciseStatus;
  preparation_starts_at?: string | null;
  filling_starts_at?: string | null;
  deadline_at?: string | null;
  closed_at?: string | null;
  is_active?: boolean;
};

export type BudgetContext = {
  exercise: BudgetExercise | null;
  guidance: {
    current_version: number | null;
    guidance_id?: string | null;
    title?: string | null;
    acknowledged: boolean;
    acknowledged_at?: string | null;
    published_at?: string | null;
  };
  scopes: UserScope[];
  capabilities: {
    access: boolean;
    guidance_view: boolean;
    guidance_manage: boolean;
    scopes_manage: boolean;
    admin: boolean;
  };
  modules_unlocked: boolean;
  reason?: string | null;
};

export type GuidancePremise = {
  id?: string;
  name: string;
  value_text?: string | null;
  value_numeric?: string | number | null;
  unit_label?: string | null;
  description?: string | null;
  display_order?: number;
  active?: boolean;
};

export type GuidanceScheduleItem = {
  id?: string;
  title: string;
  description?: string | null;
  starts_on: string;
  ends_on?: string | null;
  display_order?: number;
  highlighted?: boolean;
};

export type GuidanceCurrent = {
  id: string;
  version_number: number;
  title: string;
  board_message: string;
  sender_name?: string | null;
  sender_role?: string | null;
  objective: string;
  general_guidance: string;
  additional_notes?: string | null;
  premises: GuidancePremise[];
  schedule: GuidanceScheduleItem[];
  published_at?: string | null;
  acknowledged?: boolean;
  acknowledged_at?: string | null;
  exercise?: {
    id: string;
    year: number;
    name: string;
    status: ExerciseStatus;
  };
};

export type GuidanceDocument = {
  id: string;
  display_name: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  document_kind: string;
  description?: string | null;
  display_order?: number;
  status?: "active" | "archived";
  external_url?: string | null;
};

export type AdminDocumentUploadInput = {
  exerciseId: string;
  guidanceId: string;
  file?: File | null;
  displayName: string;
  description?: string;
  displayOrder?: number;
  documentKind?: string;
  externalUrl?: string;
};

export type AdminExerciseInput = {
  year: number;
  name: string;
  description?: string | null;
  preparation_starts_at?: string | null;
  filling_starts_at?: string | null;
  deadline_at?: string | null;
  closed_at?: string | null;
};

export type AdminExercisePatch = Partial<Omit<AdminExerciseInput, "year">> & {
  status?: ExerciseStatus;
};

export type AdminGuidanceBundle = {
  draft: GuidanceCurrent & { status: "draft" | "published" };
  published_versions: Array<{
    id: string;
    version_number: number;
    title: string;
    published_at?: string | null;
  }>;
};

export type UserScope = {
  id: string;
  user_sub: string;
  user_name?: string | null;
  user_email?: string | null;
  unit_code: string;
  area_code?: string | null;
  cost_center_code?: string | null;
  scope_level: string;
  role_in_scope?: string;
  active: boolean;
};

export type UserScopeInput = {
  user_sub: string;
  user_name?: string | null;
  user_email?: string | null;
  unit_code: string;
  area_code?: string | null;
  cost_center_code?: string | null;
  scope_level: string;
  role_in_scope?: string;
};

export type OrgCostCenter = {
  id?: string;
  branch?: string | null;
  code: string;
  name: string;
  description?: string | null;
  unit_code?: string | null;
  area_code?: string | null;
  source?: "manual" | "erp" | string | null;
  active?: boolean;
};

export type ErpCostCenter = {
  branch: string;
  code: string;
  description: string;
};

export type OrgCatalog = {
  units: Array<{ code: string; name: string; active?: boolean }>;
  areas: Array<{ code: string; name: string; unit_code?: string | null; active?: boolean }>;
  cost_centers: OrgCostCenter[];
};

export type PagedItems<T> = {
  items: T[];
};

export type ResponsibilityType = "owner" | "collaborator";

export type BudgetResponsibility = {
  id: string;
  exercise_id: string;
  module: string;
  user_sub: string;
  user_name_snapshot?: string | null;
  user_email_snapshot?: string | null;
  unit_id: string;
  branch?: string | null;
  area_id?: string | null;
  cost_center_id: string;
  responsibility_type: ResponsibilityType;
  valid_from?: string | null;
  valid_until?: string | null;
  is_active: boolean;
  created_by?: string;
  created_at?: string;
  updated_by?: string | null;
  updated_at?: string | null;
  deactivated_by?: string | null;
  deactivated_at?: string | null;
  deactivation_reason?: string | null;
};

export type BudgetResponsibilityCreateInput = {
  exercise_id: string;
  module?: string;
  user_sub: string;
  user_name_snapshot?: string | null;
  user_email_snapshot?: string | null;
  unit_id: string;
  area_id?: string | null;
  cost_center_id: string;
  responsibility_type: ResponsibilityType;
  valid_from?: string | null;
  valid_until?: string | null;
};

export type BudgetResponsibilityUpdateInput = {
  responsibility_type?: ResponsibilityType;
  valid_from?: string | null;
  valid_until?: string | null;
  user_name_snapshot?: string | null;
  user_email_snapshot?: string | null;
};

export type BudgetResponsibilityListFilters = {
  exercise_id?: string;
  module?: string;
  user_sub?: string;
  unit_id?: string;
  area_id?: string;
  cost_center_id?: string;
  is_active?: boolean | null;
  /** Filtro server-side (query `responsibility_type`). */
  responsibility_type?: ResponsibilityType | "";
  page?: number;
  page_size?: number;
};

export type CapexCategory = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  display_order: number;
  is_active: boolean;
  is_system_default: boolean;
  created_by?: string;
  created_at?: string;
  updated_by?: string | null;
  updated_at?: string | null;
  deactivated_by?: string | null;
  deactivated_at?: string | null;
};

export type CapexCategoryCreateInput = {
  code: string;
  name: string;
  description?: string | null;
  display_order?: number;
};

export type CapexCategoryUpdateInput = {
  name?: string;
  description?: string | null;
  display_order?: number;
};

export type CapexCategoryListResult = {
  items: CapexCategory[];
};

export type CapexInvestmentStatus = "draft" | "archived";
export type CapexPriority = "1" | "2" | "3" | "4";
export type CapexOrigin = "national" | "imported";
export type CapexClassification = "1" | "2" | "3" | "4" | "5" | "6";
export type CapexShift = "1" | "2" | "3";

export type CapexInvestment = {
  id: string;
  exercise_id: string;
  unit_id: string;
  area_id?: string | null;
  cost_center_id: string;
  category_id?: string | null;
  accounting_account_code?: string | null;
  description?: string | null;
  justification?: string | null;
  probable_supplier_name?: string | null;
  probable_supplier_code?: string | null;
  /** Decimal serializado como string (nunca float). */
  estimated_amount?: string | null;
  currency: string;
  required_date?: string | null;
  priority?: CapexPriority | string | null;
  origin?: CapexOrigin | string | null;
  classification?: CapexClassification | string | null;
  shift?: CapexShift | string | null;
  application?: string | null;
  observations?: string | null;
  status: CapexInvestmentStatus | string;
  version: number;
  created_by?: string;
  created_at?: string;
  updated_by?: string | null;
  updated_at?: string | null;
  archived_by?: string | null;
  archived_at?: string | null;
  is_complete: boolean;
  missing_fields: string[];
};

export type CapexInvestmentCreateInput = {
  exercise_id: string;
  cost_center_id: string;
  unit_id?: string | null;
  area_id?: string | null;
  category_id?: string | null;
  description?: string | null;
  justification?: string | null;
  probable_supplier_name?: string | null;
  probable_supplier_code?: string | null;
  estimated_amount?: string | null;
  currency?: string;
  required_date?: string | null;
  priority?: string | null;
  origin?: string | null;
  classification?: string | null;
  shift?: string | null;
  application?: string | null;
  observations?: string | null;
};

export type CapexInvestmentUpdateInput = {
  version: number;
  cost_center_id?: string | null;
  category_id?: string | null;
  description?: string | null;
  justification?: string | null;
  probable_supplier_name?: string | null;
  probable_supplier_code?: string | null;
  estimated_amount?: string | null;
  currency?: string | null;
  required_date?: string | null;
  priority?: string | null;
  origin?: string | null;
  classification?: string | null;
  shift?: string | null;
  application?: string | null;
  observations?: string | null;
};

export type CapexInvestmentListFilters = {
  exercise_id?: string;
  unit_id?: string;
  cost_center_id?: string;
  category_id?: string;
  priority?: string;
  origin?: string;
  status?: string;
  q?: string;
  page?: number;
  page_size?: number;
};

export type CapexInvestmentListResult = {
  items: CapexInvestment[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    has_more: boolean;
  };
};

export type CapexAttachmentType =
  | "quotation"
  | "commercial_proposal"
  | "technical_specification"
  | "image"
  | "justification"
  | "other";

export type CapexInvestmentAttachment = {
  id: string;
  investment_id: string;
  attachment_type: CapexAttachmentType | string;
  display_name: string;
  description?: string | null;
  original_filename: string;
  mime_type: string;
  file_size: number;
  created_by?: string;
  created_at?: string;
  archived_by?: string | null;
  archived_at?: string | null;
  is_active: boolean;
};

export type CapexAttachmentUploadInput = {
  investmentId: string;
  file: File;
  attachmentType: CapexAttachmentType | string;
  displayName: string;
  description?: string;
  idempotencyKey: string;
};

/** Status do planejamento CAPEX por exercício + centro de custo (Fase 2C). */
export type CapexPlanStatus =
  | "draft"
  | "submitted"
  | "changes_requested"
  | "rejected"
  | "approved";

export type CapexPlanHistoryAction =
  | "created"
  | "submitted"
  | "request_changes"
  | "rejected"
  | "approved";

export type CapexPlan = {
  id: string;
  exercise_id: string;
  unit_id: string;
  branch?: string | null;
  area_id?: string | null;
  cost_center_id: string;
  status: CapexPlanStatus | string;
  version: number;
  submitted_by?: string | null;
  submitted_at?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  decision_comment?: string | null;
  created_by?: string;
  created_at?: string;
  updated_by?: string | null;
  updated_at?: string | null;
  /** Presente em get/review detail. */
  investments?: CapexInvestment[];
};

export type CapexPlanHistoryEntry = {
  id: string;
  plan_id: string;
  action: CapexPlanHistoryAction | string;
  previous_status?: CapexPlanStatus | string | null;
  new_status: CapexPlanStatus | string;
  comment?: string | null;
  actor_sub: string;
  actor_name?: string | null;
  created_at: string;
};

export type CapexPlanHistoryResult = {
  items: CapexPlanHistoryEntry[];
};

export type CapexPlanListFilters = {
  exercise_id?: string;
  unit_id?: string;
  area_id?: string;
  cost_center_id?: string;
  status?: string;
  submitted_by?: string;
  page?: number;
  page_size?: number;
};

export type CapexPlanListResult = {
  items: CapexPlan[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    has_more: boolean;
  };
};

export type CapexPlanIncompleteInvestment = {
  id?: string | null;
  description?: string | null;
  missing_fields?: string[];
  reason?: string;
};

export type BudgetResponsibilityListResult = {
  items: BudgetResponsibility[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    has_more: boolean;
  };
};

export type MyResponsibilitiesResult = {
  user_sub: string;
  module: string;
  items: BudgetResponsibility[];
};

/** Filtros da consolidação gerencial CAPEX (Fase 2D.2). */
export type CapexConsolidationFilters = {
  exercise_id?: string;
  year?: number;
  unit_id?: string;
  area_id?: string;
  cost_center_id?: string;
  category_id?: string;
  priority?: string;
  origin?: string;
  plan_status?: string;
  required_date_from?: string;
  required_date_to?: string;
};

export type CapexConsolidationSummaryMetrics = {
  currency: string;
  total_estimated_amount: string;
  investment_count: number;
  cost_center_count: number;
  plans_draft_count: number;
  plans_submitted_count: number;
  plans_changes_requested_count: number;
  plans_rejected_count: number;
  plans_approved_count: number;
  approved_amount: string;
  in_review_amount: string;
  incomplete_investment_count: number;
};

export type CapexConsolidationSummaryResult = {
  exercise: {
    id: string;
    year?: number;
    name?: string;
    status?: string;
  };
  filters: Record<string, unknown>;
  summary: CapexConsolidationSummaryMetrics;
};

export type CapexConsolidationGroupItem = {
  code: string;
  description: string;
  investment_count: number;
  total_amount: string;
  percent_of_total?: string | null;
  unit_id?: string | null;
  area_id?: string | null;
  cost_center_id?: string | null;
  plan_status?: string | null;
  plan_status_label?: string | null;
};

export type CapexConsolidationGroupingResult = {
  exercise: {
    id: string;
    year?: number;
    name?: string;
  };
  filters: Record<string, unknown>;
  group_by: string;
  currency: string;
  total_estimated_amount: string;
  items: CapexConsolidationGroupItem[];
};

export type CapexConsolidationDetailItem = {
  id: string;
  exercise_id: string;
  unit_id?: string | null;
  unit_name?: string | null;
  area_id?: string | null;
  area_name?: string | null;
  cost_center_id?: string | null;
  cost_center_name?: string | null;
  responsible?: string | null;
  description?: string | null;
  category_id?: string | null;
  category_code?: string | null;
  category_name?: string | null;
  priority?: string | null;
  priority_label?: string | null;
  origin?: string | null;
  origin_label?: string | null;
  probable_supplier_name?: string | null;
  probable_supplier_code?: string | null;
  estimated_amount: string;
  currency?: string | null;
  required_date?: string | null;
  is_complete: boolean;
  missing_fields?: string[];
  plan_status?: string | null;
  plan_status_label?: string | null;
  plan_id?: string | null;
  updated_at?: string | null;
  created_at?: string | null;
};

export type CapexConsolidationDetailsResult = {
  exercise: {
    id: string;
    year?: number;
    name?: string;
  };
  filters: Record<string, unknown>;
  items: CapexConsolidationDetailItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};

export type CapexConsolidationExportResult = {
  blob: Blob;
  filename: string;
};

/** Orçamento de Pessoal (Fase 3B.1.1 / 3B.2) — cargo livre. */
export type PersonnelHeadcountField =
  | "headcount_dec_2025"
  | "headcount_oct_2026"
  | "headcount_forecast"
  | "headcount_dec_2027";

export type PersonnelPlanLine = {
  id: string;
  plan_id: string;
  position_name: string;
  headcount_dec_2025?: number | null;
  headcount_oct_2026?: number | null;
  headcount_forecast?: number | null;
  headcount_dec_2027?: number | null;
  observations?: string | null;
  version: number;
  is_active?: boolean;
  is_complete?: boolean;
  missing_fields?: string[];
  created_by?: string;
  created_at?: string;
  updated_by?: string | null;
  updated_at?: string | null;
};

export type PersonnelPlanTotals = {
  headcount_dec_2025: number;
  headcount_oct_2026: number;
  headcount_forecast: number;
  headcount_dec_2027: number;
};

export type PersonnelPlanStatus =
  | "draft"
  | "submitted"
  | "changes_requested"
  | "rejected"
  | "approved";

export type PersonnelPlanHistoryAction =
  | "created"
  | "submitted"
  | "request_changes"
  | "rejected"
  | "approved";

export type PersonnelPlan = {
  id: string;
  exercise_id: string;
  unit_id: string;
  branch?: string | null;
  area_id?: string | null;
  cost_center_id: string;
  status: PersonnelPlanStatus | string;
  version: number;
  submitted_by?: string | null;
  submitted_at?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  decision_comment?: string | null;
  lines: PersonnelPlanLine[];
  position_count: number;
  totals: PersonnelPlanTotals;
  incomplete_line_count: number;
  is_complete: boolean;
  missing_fields?: string[];
  created_by?: string;
  created_at?: string;
  updated_by?: string | null;
  updated_at?: string | null;
};

export type PersonnelPlanHistoryEntry = {
  id: string;
  plan_id: string;
  action: PersonnelPlanHistoryAction | string;
  previous_status?: PersonnelPlanStatus | string | null;
  new_status: PersonnelPlanStatus | string;
  comment?: string | null;
  actor_sub: string;
  actor_name?: string | null;
  created_at: string;
};

export type PersonnelPlanHistoryResult = {
  items: PersonnelPlanHistoryEntry[];
};

export type PersonnelPlanListFilters = {
  exercise_id?: string;
  unit_id?: string;
  area_id?: string;
  cost_center_id?: string;
  status?: string;
  submitted_by?: string;
  page?: number;
  page_size?: number;
};

export type PersonnelPlanIncompleteLine = {
  id?: string | null;
  position_name?: string | null;
  missing_fields?: string[];
};

export type PersonnelPlanListResult = {
  items: PersonnelPlan[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    has_more: boolean;
  };
};

export type PersonnelPlanResolveInput = {
  exercise_id: string;
  unit_id: string;
  cost_center_id: string;
};

export type PersonnelPlanLineCreateInput = {
  position_name: string;
  headcount_dec_2025?: number | null;
  headcount_oct_2026?: number | null;
  headcount_forecast?: number | null;
  headcount_dec_2027?: number | null;
  observations?: string | null;
};

export type PersonnelPlanLineUpdateInput = {
  version: number;
  position_name?: string;
  headcount_dec_2025?: number | null;
  headcount_oct_2026?: number | null;
  headcount_forecast?: number | null;
  headcount_dec_2027?: number | null;
  observations?: string | null;
};
