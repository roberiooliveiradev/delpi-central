import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type { PedidosVendaAbertosData } from "../types/pedidosVendaAbertos";
import { httpGet } from "./httpClient";

export const PEDIDOS_VENDA_ABERTOS_API_BASE = "/apps/api-delpi/pedidos-venda-abertos";

export async function getPedidosVendaAbertos(
  signal?: AbortSignal,
): Promise<PedidosVendaAbertosData> {
  const response = await httpGet<ApiSuccessResponse<PedidosVendaAbertosData>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar pedidos de venda em aberto.");
}
