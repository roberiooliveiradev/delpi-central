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
import type { CreatePlanPayload } from "../types/planForm";

const API_BASE = "/apps/api-delpi/quality/action-plans";

type ListParams = {
  status?: string;
  severity?: string;
  product_code?: string;
  customer_name?: string;
  branch_code?: string;
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
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function fetchDashboard(branchCode?: string): Promise<DashboardSummary> {
  const query = branchCode ? `?branch_code=${encodeURIComponent(branchCode)}` : "";
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

export async function fetchActionPlanDetail(planId: string): Promise<ActionPlanDetail> {
  const envelope = await httpGet<ApiEnvelope<ActionPlanDetail>>(`${API_BASE}/${planId}`);
  return unwrapApiDelpiEnvelope(envelope, "Erro ao carregar plano de ação.");
}

export async function createActionPlan(payload: CreatePlanPayload): Promise<ActionPlanSummary> {
  const envelope = await httpPost<ApiEnvelope<ActionPlanSummary>>(API_BASE, payload);
  return unwrapApiDelpiEnvelope(envelope, "Erro ao criar plano de ação.");
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
