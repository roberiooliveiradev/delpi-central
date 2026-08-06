import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import { apiDelpiUrl, httpPost } from "./httpClient";

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
    apiDelpiUrl("/pedidos-venda-abertos/customers/billing-series"),
    {
      customers,
      months: options?.months ?? 12,
    },
    { signal: options?.signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar faturamento mensal.");
}
