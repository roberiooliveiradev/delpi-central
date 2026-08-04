import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import { httpDelete, httpGetBlob, httpPost, httpPutFormData } from "./httpClient";
import { PEDIDOS_VENDA_ABERTOS_API_BASE } from "./pedidosVendaAbertosApi";

export type CustomerBillingTrend = "up" | "down" | "stable" | "insufficient";

export type CustomerEnrichmentItem = {
  customer_code: string;
  customer_store: string;
  city: string | null;
  state: string | null;
  last_purchase_date: string | null;
  billed_12m: number;
  billed_recent_6m?: number;
  billed_prior_6m?: number;
  billing_trend?: CustomerBillingTrend;
  billing_trend_pct?: number | null;
  has_avatar: boolean;
  avatar_url: string | null;
};

export function customerAvatarUrl(code: string, store: string): string {
  return `${PEDIDOS_VENDA_ABERTOS_API_BASE}/customers/${encodeURIComponent(code)}/${encodeURIComponent(store)}/avatar`;
}

export async function enrichPortfolioCustomers(
  customers: Array<{ customer_code: string; customer_store: string }>,
  signal?: AbortSignal,
): Promise<CustomerEnrichmentItem[]> {
  if (customers.length === 0) return [];
  const response = await httpPost<ApiSuccessResponse<{ items?: CustomerEnrichmentItem[] }>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/customers/enrichment`,
    { customers },
    { signal },
  );
  const data = unwrapApiDelpiEnvelope(response, "Erro ao enriquecer clientes.");
  return data.items ?? [];
}

export async function upsertCustomerAvatar(
  code: string,
  store: string,
  file: File,
): Promise<{ has_avatar: boolean }> {
  const form = new FormData();
  form.append("file", file);
  const response = await httpPutFormData<
    ApiSuccessResponse<{ has_avatar?: boolean }>
  >(customerAvatarUrl(code, store), form);
  return unwrapApiDelpiEnvelope(response, "Erro ao salvar logo do cliente.");
}

export async function deleteCustomerAvatar(code: string, store: string): Promise<void> {
  const response = await httpDelete<ApiSuccessResponse<{ has_avatar?: boolean }>>(
    customerAvatarUrl(code, store),
  );
  unwrapApiDelpiEnvelope(response, "Erro ao remover logo do cliente.");
}

export async function fetchCustomerAvatarObjectUrl(
  code: string,
  store: string,
  signal?: AbortSignal,
): Promise<string | null> {
  try {
    const blob = await httpGetBlob(customerAvatarUrl(code, store), { signal });
    return URL.createObjectURL(blob);
  } catch {
    return null;
  }
}
