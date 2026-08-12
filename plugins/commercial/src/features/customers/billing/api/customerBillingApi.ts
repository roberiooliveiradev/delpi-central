import { unwrapEnvelope, type ApiSuccessResponse } from "../../../../types/api.ts";
import { commercialApiUrl, httpGet } from "../../../../api/httpClient.ts";
import type {
  CustomerBillingData,
  CustomerBillingSituationFilter,
} from "../types/customerBilling";

export type CustomerBillingQuery = {
  codigo: string;
  loja: string;
  startDate: string;
  endDate: string;
  page: number;
  pageSize: number;
  situation: CustomerBillingSituationFilter;
  search: string;
};

function encodeSegment(value: string): string {
  return encodeURIComponent(value.trim());
}

export function buildCustomerBillingPath(query: CustomerBillingQuery): string {
  const params = new URLSearchParams();
  params.set("start_date", query.startDate);
  params.set("end_date", query.endDate);
  params.set("page", String(query.page));
  params.set("page_size", String(query.pageSize));
  params.set("situation", query.situation);
  if (query.search.trim()) {
    params.set("search", query.search.trim());
  }
  return (
    `${commercialApiUrl(
      `/customers/${encodeSegment(query.codigo)}/${encodeSegment(query.loja)}/outbound-invoices`,
    )}?${params.toString()}`
  );
}

export async function getCustomerOutboundInvoices(
  query: CustomerBillingQuery,
  signal?: AbortSignal,
): Promise<CustomerBillingData> {
  const response = await httpGet<ApiSuccessResponse<CustomerBillingData>>(
    buildCustomerBillingPath(query),
    { signal },
  );
  return unwrapEnvelope(
    response,
    "Erro ao carregar faturamento e notas fiscais do cliente.",
  );
}
