import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  EficienciaFabrilDashboardData,
  EficienciaFabrilFilterParams,
  EficienciaFabrilItem,
} from "../types/eficienciaFabril";
import { httpGet } from "./httpClient";

export const EFICIENCIA_FABRIL_API_BASE = "/apps/api-delpi/production";

function buildQuery(params: EficienciaFabrilFilterParams): string {
  const searchParams = new URLSearchParams();

  searchParams.set("start_date", params.start_date);
  searchParams.set("end_date", params.end_date);

  if (params.branch) searchParams.set("branch", params.branch);
  if (params.status_ok_only !== undefined) {
    searchParams.set("status_ok_only", String(params.status_ok_only));
  }
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));

  return `?${searchParams.toString()}`;
}

export async function getEficienciaFabrilDashboard(
  params: EficienciaFabrilFilterParams,
  signal?: AbortSignal
): Promise<EficienciaFabrilDashboardData> {
  const response = await httpGet<ApiSuccessResponse<EficienciaFabrilDashboardData>>(
    `${EFICIENCIA_FABRIL_API_BASE}/eficiencia-fabril/dashboard${buildQuery(params)}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar dashboard");
}

export async function getEficienciaFabrilAppointments(
  params: Omit<EficienciaFabrilFilterParams, "page" | "page_size">,
  signal?: AbortSignal
): Promise<EficienciaFabrilItem[]> {
  const response = await httpGet<ApiSuccessResponse<EficienciaFabrilItem[]>>(
    `${EFICIENCIA_FABRIL_API_BASE}/eficiencia-fabril/appointments${buildQuery(params)}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar apontamentos");
}
