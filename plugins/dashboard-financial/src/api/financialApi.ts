import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  EbitdaPctData,
  FinancialFilterParams,
  FixedCostPctData,
  PmrData,
  RolData,
} from "../types/financial";

export const FINANCIAL_API_BASE = "/apps/api-delpi/financial";

function buildQuery(params: FinancialFilterParams = {}): string {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set("start_date", params.start_date);
  if (params.end_date) searchParams.set("end_date", params.end_date);
  if (params.branch) searchParams.set("branch", params.branch);

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchFinancialData<T>(
  path: string,
  params: FinancialFilterParams = {},
  signal?: AbortSignal
): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${FINANCIAL_API_BASE}${path}${buildQuery(params)}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro na API financeira");
}

export function getRol(params: FinancialFilterParams, signal?: AbortSignal) {
  return fetchFinancialData<RolData>("/rol", params, signal);
}

export function getEbitdaPct(params: FinancialFilterParams, signal?: AbortSignal) {
  return fetchFinancialData<EbitdaPctData>("/ebitda_pct", params, signal);
}

export function getFixedCostPct(
  params: FinancialFilterParams,
  signal?: AbortSignal
) {
  return fetchFinancialData<FixedCostPctData>("/fixed_cost_pct", params, signal);
}

export function getPmr(params: FinancialFilterParams, signal?: AbortSignal) {
  return fetchFinancialData<PmrData>("/pmr", params, signal);
}
