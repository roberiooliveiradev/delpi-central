import { unwrapEnvelope, type ApiSuccessResponse } from "../../../../types/api.ts";
import { commercialApiUrl, httpGet } from "../../../../api/httpClient.ts";
import type {
  CustomerBillingData,
  CustomerBillingSituationFilter,
  CustomerInvoice,
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

export async function getCustomerOutboundInvoice(
  params: {
    codigo: string;
    loja: string;
    branch: string;
    invoiceNumber: string;
    invoiceSeries: string;
  },
  signal?: AbortSignal,
): Promise<CustomerInvoice> {
  const path =
    `${commercialApiUrl(
      `/customers/${encodeSegment(params.codigo)}/${encodeSegment(params.loja)}/outbound-invoices/${encodeSegment(params.branch)}/${encodeSegment(params.invoiceNumber)}/${encodeSegment(params.invoiceSeries)}`,
    )}`;
  const response = await httpGet<ApiSuccessResponse<CustomerInvoice>>(path, {
    signal,
  });
  return unwrapEnvelope(response, "Erro ao carregar a nota fiscal do cliente.");
}
