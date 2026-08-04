import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type { OpsAbertasData } from "../types/opsAbertas";
import type { PedidosVendaAbertosData } from "../types/pedidosVendaAbertos";
import { httpGet } from "./httpClient";

export const PEDIDOS_VENDA_ABERTOS_API_BASE = "/apps/api-delpi/pedidos-venda-abertos";

export async function getPedidosVendaAbertos(
  signal?: AbortSignal,
  options?: { sellerId?: string | null },
): Promise<PedidosVendaAbertosData> {
  const params = new URLSearchParams();
  if (options?.sellerId) {
    params.set("seller_id", options.sellerId);
  }
  const qs = params.toString();
  const response = await httpGet<ApiSuccessResponse<PedidosVendaAbertosData>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/${qs ? `?${qs}` : ""}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar pedidos de venda em aberto.");
}

export async function getOpsAbertas(signal?: AbortSignal): Promise<OpsAbertasData> {
  const response = await httpGet<ApiSuccessResponse<OpsAbertasData>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/ops-abertas`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar OPs abertas.");
}
