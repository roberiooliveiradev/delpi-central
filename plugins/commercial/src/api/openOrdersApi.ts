import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type { OpenOrdersData } from "../types/openOrders";
import { apiDelpiUrl, httpGet } from "./httpClient";

const OPEN_ORDERS_PATH = "/pedidos-venda-abertos";

export async function getOpenOrders(
  signal?: AbortSignal,
  options?: { sellerId?: string | null },
): Promise<OpenOrdersData> {
  const params = new URLSearchParams();
  if (options?.sellerId) {
    params.set("seller_id", options.sellerId);
  }
  const qs = params.toString();
  // Barra final obrigatória: sem ela o FastAPI redireciona e, atrás do
  // proxy HTTPS, o Location pode vir em http:// → Mixed Content no browser.
  const response = await httpGet<ApiSuccessResponse<OpenOrdersData>>(
    `${apiDelpiUrl(OPEN_ORDERS_PATH)}/${qs ? `?${qs}` : ""}`,
    { signal },
  );

  return unwrapEnvelope(response, "Erro ao carregar pedidos em aberto.");
}

export function resolveOrderStatus(item: OpenOrdersData["items"][number]): string {
  if (item.status?.trim()) return item.status.trim();
  if (item.tipo_pedido?.trim()) return item.tipo_pedido.trim();
  return "Em aberto";
}
