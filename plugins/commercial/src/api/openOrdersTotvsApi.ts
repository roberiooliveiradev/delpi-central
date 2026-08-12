import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type { OpsAbertasData } from "../types/openOps";
import type { OpenOrdersTotvsData } from "../types/openOrdersTotvs";
import { commercialApiUrl, httpGet } from "./httpClient";

/** Base path do BFF commercial (escopo + proxy TOTVS). */
export const OPEN_ORDERS_TOTVS_API_BASE = "/apps/commercial-api/open-orders";

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
    `${commercialApiUrl("/open-orders/")}${qs ? `?${qs}` : ""}`,
    { signal },
  );

  return unwrapEnvelope(response, "Erro ao carregar pedidos de venda em aberto.");
}

export async function getOpsAbertas(signal?: AbortSignal): Promise<OpsAbertasData> {
  const response = await httpGet<ApiSuccessResponse<OpsAbertasData>>(
    commercialApiUrl("/open-orders/ops-abertas"),
    { signal },
  );

  return unwrapEnvelope(response, "Erro ao carregar OPs abertas.");
}
