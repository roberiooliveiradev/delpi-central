import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type { CustomerBillingData, CustomerBillingSeriesPayload } from "../types/billing";
import { apiDelpiUrl, httpGet, httpPost } from "./httpClient";

const PEDIDOS_VENDA_ABERTOS_PATH = "/pedidos-venda-abertos";

export async function fetchCustomerBillingSeries(
  customers: Array<{ customer_code: string; customer_store: string }>,
  options?: { months?: number; signal?: AbortSignal },
): Promise<CustomerBillingSeriesPayload> {
  const response = await httpPost<ApiSuccessResponse<CustomerBillingSeriesPayload>>(
    apiDelpiUrl(`${PEDIDOS_VENDA_ABERTOS_PATH}/customers/billing-series`),
    { customers, months: options?.months ?? 12 },
    { signal: options?.signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar faturamento mensal.");
}

export async function getCustomerOutboundInvoices(
  codigo: string,
  loja: string,
  options?: {
    startDate?: string;
    endDate?: string;
    page?: number;
    pageSize?: number;
    situation?: "all" | "emitted" | "return";
    signal?: AbortSignal;
  },
): Promise<CustomerBillingData> {
  const params = new URLSearchParams();
  if (options?.startDate) params.set("start_date", options.startDate);
  if (options?.endDate) params.set("end_date", options.endDate);
  params.set("page", String(options?.page ?? 1));
  params.set("page_size", String(options?.pageSize ?? 20));
  params.set("situation", options?.situation ?? "all");

  const response = await httpGet<ApiSuccessResponse<CustomerBillingData>>(
    `${apiDelpiUrl(
      `${PEDIDOS_VENDA_ABERTOS_PATH}/clientes/${encodeURIComponent(codigo)}/${encodeURIComponent(loja)}/notas-fiscais`,
    )}?${params.toString()}`,
    { signal: options?.signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar notas fiscais do cliente.");
}
