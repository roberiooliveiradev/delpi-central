import { httpGet, unwrapApiDelpiEnvelope, type ApiEnvelope } from "./httpClient";
import type {
  ActionPlanDetail,
  DashboardSummary,
  PagedPlansResponse,
} from "../types/actionPlan";

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
