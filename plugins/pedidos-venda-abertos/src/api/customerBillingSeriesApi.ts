import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import { httpPost } from "./httpClient";
import { PEDIDOS_VENDA_ABERTOS_API_BASE } from "./pedidosVendaAbertosApi";

export type CustomerBillingSeriesPoint = {
  month: string;
  label: string;
  value: number;
  date_start: string;
  date_end: string;
};

export type CustomerBillingSeriesPayload = {
  months: number;
  customer_count: number;
  points: CustomerBillingSeriesPoint[];
};

export async function fetchCustomerBillingSeries(
  customers: Array<{ customer_code: string; customer_store: string }>,
  options?: { months?: number; signal?: AbortSignal },
): Promise<CustomerBillingSeriesPayload> {
  const response = await httpPost<ApiSuccessResponse<CustomerBillingSeriesPayload>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/customers/billing-series`,
    {
      customers,
      months: options?.months ?? 12,
    },
    { signal: options?.signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar faturamento mensal.");
}
