import type { PlanEvidence, TeamMember, Rnc8dTemplatePayload } from "./rnc8d";

export type PlanStatus =
  | "draft"
  | "triage"
  | "containment"
  | "root_cause_analysis"
  | "action_plan_defined"
  | "in_progress"
  | "waiting_validation"
  | "completed"
  | "cancelled";

export type PlanSeverity = "low" | "medium" | "high" | "critical";

export type NonconformityScope = "internal" | "external";

export type ActionPlanSummary = {
  id: string;
  code?: string;
  title: string;
  customer_name?: string | null;
  customer_code?: string | null;
  customer_store?: string | null;
  product_code?: string | null;
  customer_product_reference?: string | null;
  branch_code?: string | null;
  nonconformity_scope?: NonconformityScope;
  severity: PlanSeverity;
  status: PlanStatus;
  owner_user_id?: string | null;
  created_at?: string;
  updated_at?: string;
  sla_level?: "ok" | "warning" | "breached";
  days_without_update?: number;
  sla_warning_days?: number;
  sla_breach_days?: number;
  effectiveness_approval_status?: "pending_review" | "approved" | "rejected" | null;
  effectiveness_proposed_status?: string | null;
  effectiveness_submitted_at?: string | null;
  effectiveness_submitted_by?: string | null;
  effectiveness_submitted_by_name?: string | null;
  incomplete_actions_count?: number;
};

export type Pagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type PagedPlansResponse = {
  items: ActionPlanSummary[];
  pagination: Pagination;
};

export type DashboardSummary = {
  open_plans: number;
  critical_open: number;
  waiting_validation: number;
  completed_this_month: number;
  overdue_actions: number;
  overdue_plans: number;
  branch_code?: string;
  nonconformity_scope?: NonconformityScope;
  open_internal?: number;
  open_external?: number;
  by_branch?: Array<{
    branch_code: string;
    open_plans: number;
    critical_open: number;
  }>;
  by_scope?: Array<{
    nonconformity_scope: NonconformityScope;
    open_plans: number;
    critical_open: number;
  }>;
  timing?: DashboardTiming;
  breakdowns?: DashboardBreakdowns;
  rankings?: DashboardRankings;
  recurrence_alert?: DashboardRecurrenceAlert;
  stalled_alert?: DashboardStalledAlert;
  effectiveness_pending_alert?: DashboardEffectivenessPendingAlert;
  effectiveness_by_action_type?: DashboardEffectivenessByActionType;
};

export type DashboardTiming = {
  window_months: number;
  avg_closure_days: number | null;
  closure_sample_size: number;
  avg_time_to_effectiveness_days: number | null;
  effectiveness_sample_size: number;
};

export type DashboardBreakdownItem = {
  label: string;
  total: number;
};

export type DashboardBreakdowns = {
  window_months: number;
  by_root_cause: DashboardBreakdownItem[];
  by_failure_mode: DashboardBreakdownItem[];
  by_action_type: DashboardBreakdownItem[];
};

export type DashboardRankingItem = {
  label: string;
  total: number;
  open_plans: number;
};

export type DashboardRankings = {
  window_months: number;
  by_customer: DashboardRankingItem[];
  by_product: DashboardRankingItem[];
  by_owner: DashboardRankingItem[];
};

export type DashboardRecurrenceGroupAlert = {
  recurrence_key: string;
  product_code?: string | null;
  failure_mode?: string | null;
  branch_code?: string | null;
  plans_in_window: number;
  total_plans: number;
  open_plans: number;
};

export type DashboardRecurrenceAlert = {
  window_months: number;
  groups_detected: number;
  plans_in_window: number;
  open_plans_in_recurrence: number;
  top_groups: DashboardRecurrenceGroupAlert[];
};

export type DashboardStalledPlanAlert = {
  id: string;
  code?: string | null;
  title?: string | null;
  branch_code?: string | null;
  status?: string | null;
  updated_at?: string | null;
  days_without_update: number;
};

export type DashboardStalledAlert = {
  stall_days: number;
  severity: string;
  stalled_plans: number;
  top_plans: DashboardStalledPlanAlert[];
};

export type DashboardEffectivenessPendingPlanAlert = {
  id: string;
  code?: string | null;
  title?: string | null;
  branch_code?: string | null;
  severity?: string | null;
  effectiveness_proposed_status?: string | null;
  effectiveness_submitted_at?: string | null;
  effectiveness_submitted_by?: string | null;
  effectiveness_submitted_by_name?: string | null;
};

export type DashboardEffectivenessPendingAlert = {
  pending_plans: number;
  top_plans: DashboardEffectivenessPendingPlanAlert[];
};

export type DashboardEffectivenessBucket = {
  reviewed_plans: number;
  effective_plans: number;
  partially_effective_plans: number;
  ineffective_plans: number;
  effectiveness_rate: number | null;
};

export type DashboardEffectivenessByActionTypeItem = DashboardEffectivenessBucket & {
  action_type: string;
};

export type DashboardEffectivenessByActionType = {
  window_months: number;
  overall: DashboardEffectivenessBucket;
  by_action_type: DashboardEffectivenessByActionTypeItem[];
};

export type IshikawaAnalysis = {
  machine?: string[] | null;
  method_process?: string[] | null;
  material?: string[] | null;
  manpower?: string[] | null;
  measurement?: string[] | null;
  environment?: string[] | null;
  notes?: string | null;
};

export type FiveWhyStep = {
  question: string;
  answer: string;
};

export type FiveWhysStepValue = string | FiveWhyStep;

export type FiveWhysAnalysis = {
  occurrence_whys?: FiveWhysStepValue[] | null;
  detection_whys?: FiveWhysStepValue[] | null;
  root_cause?: string | null;
  confidence_level?: string | null;
  /** @deprecated legado — use occurrence_whys */
  why_1?: string | null;
  why_2?: string | null;
  why_3?: string | null;
  why_4?: string | null;
  why_5?: string | null;
  /** @deprecated legado — use detection_whys */
  detection_why_1?: string | null;
  detection_why_2?: string | null;
  detection_why_3?: string | null;
  detection_why_4?: string | null;
  detection_why_5?: string | null;
};

export type ActionResponsible = {
  id?: string;
  user_id?: string | null;
  display_name: string;
  sort_order?: number;
};

export type PlanAction = {
  id: string;
  action_type: string;
  description: string;
  responsible_user_id?: string | null;
  responsible_name?: string | null;
  responsibles?: ActionResponsible[];
  department?: string | null;
  due_date?: string | null;
  status: string;
  cause_track?: string | null;
  created_at?: string;
  completed_at?: string;
  evidence_required?: boolean;
};

export type PlanHistoryEvent = {
  id: string;
  event_type: string;
  old_value?: string | null;
  new_value?: string | null;
  comment?: string | null;
  created_by?: string | null;
  created_by_name?: string | null;
  created_by_email?: string | null;
  created_at?: string;
};

export type PlanAuditLogEntry = {
  id: string;
  event_type: string;
  payload?: Record<string, unknown>;
  actor_user_id?: string | null;
  actor_name?: string | null;
  actor_email?: string | null;
  created_at?: string;
};

export type PagedAuditLogResponse = {
  items: PlanAuditLogEntry[];
  pagination: Pagination;
};

export type ActionPlanDetail = {
  plan: ActionPlanSummary & {
    customer_contact?: string | null;
    product_description?: string | null;
    customer_product_reference?: string | null;
    batch_number?: string | null;
    reported_problem?: string | null;
    department?: string | null;
    problem_category?: string | null;
    failure_mode?: string | null;
    root_cause_category?: string | null;
    effectiveness_status?: string | null;
    effectiveness_verified_at?: string | null;
    effectiveness_notes?: string | null;
    effectiveness_approval_status?: "pending_review" | "approved" | "rejected" | null;
    effectiveness_proposed_status?: string | null;
    effectiveness_submitted_at?: string | null;
    effectiveness_submitted_by?: string | null;
    effectiveness_submitted_by_name?: string | null;
    effectiveness_reviewed_at?: string | null;
    effectiveness_reviewed_by?: string | null;
    effectiveness_rejection_reason?: string | null;
    symptom_tags?: string[];
    source_type?: string | null;
    source_reference?: string | null;
    customer_template?: string;
    client_nc_registry?: string | null;
    template_payload?: Rnc8dTemplatePayload;
  };
  ishikawa?: IshikawaAnalysis | null;
  five_whys?: FiveWhysAnalysis | null;
  team_members?: TeamMember[];
  evidences?: PlanEvidence[];
  actions: PlanAction[];
  history: PlanHistoryEvent[];
};
