import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  ProductFactoryStatusData,
  ProductStructureData,
  ProductionAppointmentsByOpData,
  ProductionOrderByOpData,
} from "../types/productionExtras";
import { apiDelpiUrl, httpGet } from "./httpClient";

export async function fetchProductionOrderByOp(
  productionOrder: string,
  params: { branch?: string },
  signal?: AbortSignal,
): Promise<ProductionOrderByOpData> {
  const encoded = encodeURIComponent(productionOrder.trim());
  const search = new URLSearchParams();
  if (params.branch?.trim()) search.set("branch", params.branch.trim());
  const qs = search.toString();
  const response = await httpGet<ApiSuccessResponse<ProductionOrderByOpData>>(
    `${apiDelpiUrl(`/production/orders/by-op/${encoded}`)}${qs ? `?${qs}` : ""}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar OP.");
}

export async function fetchProductFactoryStatus(
  productCode: string,
  signal?: AbortSignal,
): Promise<ProductFactoryStatusData> {
  const encoded = encodeURIComponent(productCode.trim());
  const response = await httpGet<ApiSuccessResponse<ProductFactoryStatusData>>(
    apiDelpiUrl(`/products/${encoded}/factory-status`),
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar status fabril.");
}

export async function fetchAppointmentsByOp(
  params: { op: string; branch?: string; page_size?: number },
  signal?: AbortSignal,
): Promise<ProductionAppointmentsByOpData> {
  const search = new URLSearchParams();
  search.set("op", params.op.trim());
  if (params.branch?.trim()) search.set("branch", params.branch.trim());
  search.set("page", "1");
  search.set("page_size", String(params.page_size ?? 50));
  const response = await httpGet<ApiSuccessResponse<ProductionAppointmentsByOpData>>(
    `${apiDelpiUrl("/production/appointments/by-op")}?${search.toString()}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar apontamentos.");
}

export async function fetchProductStructure(
  productCode: string,
  signal?: AbortSignal,
): Promise<ProductStructureData> {
  const encoded = encodeURIComponent(productCode.trim());
  const response = await httpGet<ApiSuccessResponse<ProductStructureData>>(
    `${apiDelpiUrl(`/products/${encoded}/structure`)}?max_depth=6&page_size=200`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar estrutura do produto.");
}

/** GET que devolve null em 403/404 sem lançar (RBAC / recurso ausente). */
export async function fetchOptional<T>(
  loader: () => Promise<T>,
): Promise<{ data: T | null; forbidden: boolean; missing: boolean; error: string | null }> {
  try {
    const data = await loader();
    return { data, forbidden: false, missing: false, error: null };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    const forbidden = /403|permiss/i.test(message);
    const missing = /404|não encontr|nao encontr/i.test(message);
    return {
      data: null,
      forbidden,
      missing,
      error: forbidden || missing ? null : message,
    };
  }
}
