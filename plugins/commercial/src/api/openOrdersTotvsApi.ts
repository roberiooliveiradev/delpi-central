import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type { OpsAbertasData } from "../types/openOps";
import type { OpenOrdersTotvsData } from "../types/openOrdersTotvs";
import { apiDelpiUrl, httpGet } from "./httpClient";

export const OPEN_ORDERS_TOTVS_API_BASE = "/apps/api-delpi/pedidos-venda-abertos";

export async function getOpenOrdersTotvs(
  signal?: AbortSignal,
  options?: { sellerId?: string | null },
): Promise<OpenOrdersTotvsData> {
  const params = new URLSearchParams();
  if (options?.sellerId) {
    params.set("seller_id", options.sellerId);
  }
  const qs = params.toString();
  // Barra final obrigatória (Mixed Content atrás de HTTPS).
  const response = await httpGet<ApiSuccessResponse<OpenOrdersTotvsData>>(
    `${apiDelpiUrl("/pedidos-venda-abertos")}/${qs ? `?${qs}` : ""}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar pedidos de venda em aberto.");
}

export async function getOpsAbertas(signal?: AbortSignal): Promise<OpsAbertasData> {
  const response = await httpGet<ApiSuccessResponse<OpsAbertasData>>(
    apiDelpiUrl("/pedidos-venda-abertos/ops-abertas"),
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar OPs abertas.");
}
