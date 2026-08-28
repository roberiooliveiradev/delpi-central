import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import { commercialApiUrl, httpGet } from "./httpClient";

export type CustomerInScopeItem = {
  customer_code: string;
  customer_store: string;
  customer_name: string | null;
  open_value: number;
  has_overdue: boolean;
  has_open_orders: boolean;
};

export type CustomersInScopeData = {
  items: CustomerInScopeItem[];
  summary: {
    customer_count: number;
    open_value_total: number;
    overdue_customer_count: number;
  };
  empty_portfolio: boolean;
  message: string | null;
  metrics: {
    available: boolean;
    reason: string | null;
  };
};

/** Minha carteira: membership do escopo + métricas de aberto. */
export async function getCustomersInScope(
  signal?: AbortSignal,
  options?: { sellerId?: string | null },
): Promise<CustomersInScopeData> {
  const params = new URLSearchParams();
  if (options?.sellerId) {
    params.set("seller_id", options.sellerId);
  }
  const qs = params.toString();
  const response = await httpGet<ApiSuccessResponse<CustomersInScopeData>>(
    `${commercialApiUrl("/customers/in-scope")}${qs ? `?${qs}` : ""}`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar clientes da carteira.");
}
