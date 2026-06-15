import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type { ProductionOeeAppointmentDetailData } from "../types/productionOeeDetail";
import { EFICIENCIA_FABRIL_API_BASE } from "./eficienciaFabrilApi";
import { httpGet } from "./httpClient";

export async function getProductionOeeAppointmentById(
  appointmentId: number | string,
  options: { branch?: string } = {},
  signal?: AbortSignal
): Promise<ProductionOeeAppointmentDetailData> {
  const searchParams = new URLSearchParams();
  if (options.branch) searchParams.set("branch", options.branch);

  const encoded = encodeURIComponent(String(appointmentId).trim());
  const query = searchParams.toString();
  const suffix = query ? `?${query}` : "";

  const response = await httpGet<ApiSuccessResponse<ProductionOeeAppointmentDetailData>>(
    `${EFICIENCIA_FABRIL_API_BASE}/oee/appointments/${encoded}${suffix}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar detalhe do apontamento");
}
