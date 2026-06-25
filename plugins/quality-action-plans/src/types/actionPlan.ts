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
  product_code?: string | null;
  branch_code?: string | null;
  nonconformity_scope?: NonconformityScope;
  severity: PlanSeverity;
  status: PlanStatus;
  owner_user_id?: string | null;
  created_at?: string;
  updated_at?: string;
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
};

export type IshikawaAnalysis = {
  machine?: string | null;
  method_process?: string | null;
  material?: string | null;
  manpower?: string | null;
  measurement?: string | null;
  environment?: string | null;
  notes?: string | null;
};

export type FiveWhysAnalysis = {
  why_1?: string | null;
  why_2?: string | null;
  why_3?: string | null;
  why_4?: string | null;
  why_5?: string | null;
  detection_why_1?: string | null;
  detection_why_2?: string | null;
  detection_why_3?: string | null;
  detection_why_4?: string | null;
  detection_why_5?: string | null;
  root_cause?: string | null;
  confidence_level?: string | null;
};

export type PlanAction = {
  id: string;
  action_type: string;
  description: string;
  responsible_name?: string | null;
  department?: string | null;
  due_date?: string | null;
  status: string;
  cause_track?: string | null;
};

export type PlanHistoryEvent = {
  id: string;
  event_type: string;
  old_value?: string | null;
  new_value?: string | null;
  comment?: string | null;
  created_by?: string | null;
  created_at?: string;
};

export type ActionPlanDetail = {
  plan: ActionPlanSummary & {
    customer_contact?: string | null;
    product_description?: string | null;
    batch_number?: string | null;
    reported_problem?: string | null;
    department?: string | null;
    problem_category?: string | null;
    failure_mode?: string | null;
    root_cause_category?: string | null;
    effectiveness_status?: string | null;
    symptom_tags?: string[];
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
