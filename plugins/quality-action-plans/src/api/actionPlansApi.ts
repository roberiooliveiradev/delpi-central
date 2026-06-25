import {
  httpGet,
  httpPatch,
  httpPost,
  httpPut,
  unwrapApiDelpiEnvelope,
  type ApiEnvelope,
} from "./httpClient";
import type {
  ActionPlanDetail,
  ActionPlanSummary,
  DashboardSummary,
  FiveWhysAnalysis,
  IshikawaAnalysis,
  PagedPlansResponse,
  PlanAction,
} from "../types/actionPlan";
import type { CreatePlanPayload, UpdatePlanPayload } from "../types/planForm";
import type { PlanEvidence, Rnc8dReportPayload } from "../types/rnc8d";
import type { PlanSimilarCasesResult } from "../types/similarCases";
import type { PagedRecurrenceResponse } from "../types/recurrence";
import type { PagedSolutionPatternsResponse } from "../types/solutionPattern";
import type { PagedEvidenceSearchResponse } from "../types/evidenceSearch";

const API_BASE = "/apps/api-delpi/quality/action-plans";
const SOLUTION_PATTERNS_BASE = "/apps/api-delpi/quality/solution-patterns";

type ListParams = {
  status?: string;
  severity?: string;
  product_code?: string;
  customer_name?: string;
  branch_code?: string;
  nonconformity_scope?: string;
  page?: number;
  page_size?: number;
};

function buildQuery(params: ListParams): string {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.severity) search.set("severity", params.severity);
  if (params.product_code) search.set("product_code", params.product_code);
  if (params.customer_name) search.set("customer_name", params.customer_name);
  if (params.branch_code) search.set("branch_code", params.branch_code);
  if (params.nonconformity_scope) search.set("nonconformity_scope", params.nonconformity_scope);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function fetchDashboard(
  branchCode?: string,
  nonconformityScope?: string,
): Promise<DashboardSummary> {
  const search = new URLSearchParams();
  if (branchCode) search.set("branch_code", branchCode);
  if (nonconformityScope) search.set("nonconformity_scope", nonconformityScope);
  const query = search.toString() ? `?${search.toString()}` : "";
  const envelope = await httpGet<ApiEnvelope<DashboardSummary>>(`${API_BASE}/dashboard${query}`);
  return unwrapApiDelpiEnvelope(envelope, "Erro ao carregar dashboard PAC.");
}

export async function fetchActionPlans(params: ListParams = {}): Promise<PagedPlansResponse> {
  const envelope = await httpGet<ApiEnvelope<PagedPlansResponse>>(
    `${API_BASE}${buildQuery(params)}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar planos de ação.");
}

export async function fetchOverduePlans(params: ListParams = {}): Promise<PagedPlansResponse> {
  const envelope = await httpGet<ApiEnvelope<PagedPlansResponse>>(
    `${API_BASE}/overdue${buildQuery(params)}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar planos atrasados.");
}

type RecurrenceParams = {
  branch_code?: string;
  nonconformity_scope?: string;
  min_plans?: number;
  page?: number;
  page_size?: number;
};

export async function fetchRecurrenceGroups(
  params: RecurrenceParams = {},
): Promise<PagedRecurrenceResponse> {
  const search = new URLSearchParams();
  if (params.branch_code) search.set("branch_code", params.branch_code);
  if (params.nonconformity_scope) search.set("nonconformity_scope", params.nonconformity_scope);
  if (params.min_plans) search.set("min_plans", String(params.min_plans));
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const query = search.toString() ? `?${search.toString()}` : "";
  const envelope = await httpGet<ApiEnvelope<PagedRecurrenceResponse>>(
    `${API_BASE}/recurrence${query}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar recorrência de planos.");
}

export async function fetchActionPlanDetail(planId: string): Promise<ActionPlanDetail> {
  const envelope = await httpGet<ApiEnvelope<ActionPlanDetail>>(`${API_BASE}/${planId}`);
  return unwrapApiDelpiEnvelope(envelope, "Erro ao carregar plano de ação.");
}

export async function fetchPlanSimilarCases(planId: string): Promise<PlanSimilarCasesResult> {
  const envelope = await httpGet<ApiEnvelope<PlanSimilarCasesResult>>(
    `${API_BASE}/${planId}/similar-cases`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao carregar casos similares.");
}

type SolutionPatternParams = {
  problem_category?: string;
  failure_mode?: string;
  q?: string;
  page?: number;
  page_size?: number;
};

export async function fetchSolutionPatterns(
  params: SolutionPatternParams = {},
): Promise<PagedSolutionPatternsResponse> {
  const search = new URLSearchParams();
  if (params.problem_category) search.set("problem_category", params.problem_category);
  if (params.failure_mode) search.set("failure_mode", params.failure_mode);
  if (params.q) search.set("q", params.q);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const query = search.toString() ? `?${search.toString()}` : "";
  const envelope = await httpGet<ApiEnvelope<PagedSolutionPatternsResponse>>(
    `${SOLUTION_PATTERNS_BASE}${query}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar padrões de solução.");
}

export async function promoteSolutionPattern(planId: string) {
  const envelope = await httpPost<ApiEnvelope<Record<string, unknown>>>(
    `${API_BASE}/${planId}/promote-solution-pattern`,
    {},
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao promover padrão de solução.");
}

type EvidenceSearchParams = {
  q: string;
  plan_id?: string;
  branch_code?: string;
  section?: string;
  evidence_type?: string;
  page?: number;
  page_size?: number;
};

export async function searchEvidences(
  params: EvidenceSearchParams,
): Promise<PagedEvidenceSearchResponse> {
  const search = new URLSearchParams();
  search.set("q", params.q);
  if (params.plan_id) search.set("plan_id", params.plan_id);
  if (params.branch_code) search.set("branch_code", params.branch_code);
  if (params.section) search.set("section", params.section);
  if (params.evidence_type) search.set("evidence_type", params.evidence_type);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const envelope = await httpGet<ApiEnvelope<PagedEvidenceSearchResponse>>(
    `${API_BASE}/evidences/search?${search.toString()}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao buscar evidências.");
}

export async function createActionPlan(payload: CreatePlanPayload): Promise<ActionPlanSummary> {
  const envelope = await httpPost<ApiEnvelope<ActionPlanSummary>>(API_BASE, payload);
  return unwrapApiDelpiEnvelope(envelope, "Erro ao criar plano de ação.");
}

export async function updateActionPlan(
  planId: string,
  payload: UpdatePlanPayload,
): Promise<ActionPlanSummary> {
  const envelope = await httpPatch<ApiEnvelope<ActionPlanSummary>>(
    `${API_BASE}/${planId}`,
    payload,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao atualizar plano de ação.");
}

export async function updatePlanStatus(
  planId: string,
  status: string,
  comment?: string,
): Promise<ActionPlanSummary> {
  const envelope = await httpPatch<ApiEnvelope<ActionPlanSummary>>(
    `${API_BASE}/${planId}/status`,
    { status, comment: comment?.trim() || undefined },
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao atualizar status do plano.");
}

export async function upsertIshikawa(
  planId: string,
  body: IshikawaAnalysis,
): Promise<IshikawaAnalysis> {
  const envelope = await httpPut<ApiEnvelope<IshikawaAnalysis>>(
    `${API_BASE}/${planId}/ishikawa`,
    body,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao salvar Ishikawa.");
}

export async function upsertFiveWhys(
  planId: string,
  body: FiveWhysAnalysis,
): Promise<FiveWhysAnalysis> {
  const envelope = await httpPut<ApiEnvelope<FiveWhysAnalysis>>(
    `${API_BASE}/${planId}/five-whys`,
    body,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao salvar 5 Porquês.");
}

export type NewPlanActionPayload = {
  action_type: string;
  description: string;
  responsible_name?: string;
  department?: string;
  due_date?: string;
  status?: string;
  evidence_required?: boolean;
  cause_track?: string;
};

export async function createPlanActions(
  planId: string,
  actions: NewPlanActionPayload[],
): Promise<PlanAction[]> {
  const envelope = await httpPost<ApiEnvelope<{ items: PlanAction[] }>>(
    `${API_BASE}/${planId}/actions`,
    { actions },
  );
  const data = unwrapApiDelpiEnvelope(envelope, "Erro ao registrar ações.");
  return data.items;
}

export type UpdatePlanActionPayload = {
  description?: string;
  responsible_name?: string;
  department?: string;
  due_date?: string;
  status?: string;
  evidence_required?: boolean;
  cause_track?: string;
};

export async function updatePlanAction(
  planId: string,
  actionId: string,
  body: UpdatePlanActionPayload,
): Promise<PlanAction> {
  const envelope = await httpPatch<ApiEnvelope<PlanAction>>(
    `${API_BASE}/${planId}/actions/${actionId}`,
    body,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao atualizar ação.");
}

export async function recordEffectivenessReview(
  planId: string,
  effectivenessStatus: string,
  notes?: string,
): Promise<ActionPlanSummary> {
  const envelope = await httpPost<ApiEnvelope<ActionPlanSummary>>(
    `${API_BASE}/${planId}/effectiveness-review`,
    {
      effectiveness_status: effectivenessStatus,
      notes: notes?.trim() || undefined,
    },
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao registrar eficácia.");
}

export async function upsertRnc8dReport(
  planId: string,
  body: Rnc8dReportPayload,
): Promise<ActionPlanDetail> {
  const envelope = await httpPut<ApiEnvelope<ActionPlanDetail>>(
    `${API_BASE}/${planId}/rnc-8d`,
    body,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao salvar relatório 8D.");
}

export async function exportRnc8dSpreadsheet(planId: string, filename: string): Promise<void> {
  const { httpDownloadBlob } = await import("./httpClient");
  const blob = await httpDownloadBlob(`${API_BASE}/${planId}/export/rnc-8d`);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function fetchPlanEvidences(planId: string): Promise<PlanEvidence[]> {
  const envelope = await httpGet<ApiEnvelope<PlanEvidence[]>>(
    `${API_BASE}/${planId}/evidences`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar evidências.");
}

export async function uploadPlanEvidence(
  planId: string,
  file: File,
  options: {
    evidenceType: string;
    section?: string;
    actionId?: string;
    description?: string;
    knowledgeVisible?: boolean;
  },
): Promise<PlanEvidence> {
  const { httpPostForm } = await import("./httpClient");
  const formData = new FormData();
  formData.append("file", file);
  formData.append("evidence_type", options.evidenceType);
  formData.append("section", options.section ?? "general");
  if (options.actionId) formData.append("action_id", options.actionId);
  if (options.description) formData.append("description", options.description);
  formData.append("knowledge_visible", String(options.knowledgeVisible ?? true));
  const envelope = await httpPostForm<ApiEnvelope<PlanEvidence>>(
    `${API_BASE}/${planId}/evidences`,
    formData,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao anexar evidência.");
}

export async function deletePlanEvidence(planId: string, evidenceId: string): Promise<void> {
  const { httpDelete } = await import("./httpClient");
  const envelope = await httpDelete<ApiEnvelope<{ id: string; deleted: boolean }>>(
    `${API_BASE}/${planId}/evidences/${evidenceId}`,
  );
  unwrapApiDelpiEnvelope(envelope, "Erro ao remover evidência.");
}

export async function downloadPlanEvidenceFile(planId: string, evidenceId: string, filename: string): Promise<void> {
  const { httpDownloadBlob } = await import("./httpClient");
  const blob = await httpDownloadBlob(`${API_BASE}/${planId}/evidences/${evidenceId}/file`);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
