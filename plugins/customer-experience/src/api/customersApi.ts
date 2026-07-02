import { httpGet, type ApiEnvelope } from "./httpClient";
import type { Customer, CustomerSearchResult } from "../types";

// Rota canônica de clientes TOTVS (SA1) exposta pela api-delpi via gateway.
const CUSTOMERS_SEARCH = "/apps/api-delpi/customers/search";

type RawCustomer = {
  code?: string | null;
  store?: string | null;
  name?: string | null;
  blocked?: string | null;
};

type RawCustomerPage = {
  items?: RawCustomer[];
  page?: number;
  page_size?: number;
  total?: number;
  total_pages?: number;
};

function normalizeCustomer(raw: RawCustomer): Customer {
  return {
    code: (raw.code ?? "").trim(),
    store: (raw.store ?? "").trim(),
    name: (raw.name ?? "").trim(),
    blocked: raw.blocked ?? null,
  };
}

export type CustomerSearchParams = {
  code?: string;
  name?: string;
  store?: string;
  page?: number;
  pageSize?: number;
};

export async function searchCustomers(
  params: CustomerSearchParams,
  signal?: AbortSignal,
): Promise<CustomerSearchResult> {
  const query = new URLSearchParams();
  if (params.code?.trim()) query.set("code", params.code.trim());
  if (params.name?.trim()) query.set("name", params.name.trim());
  if (params.store?.trim()) query.set("store", params.store.trim());
  query.set("page", String(params.page ?? 1));
  query.set("page_size", String(params.pageSize ?? 20));

  const response = await httpGet<ApiEnvelope<RawCustomerPage>>(
    `${CUSTOMERS_SEARCH}?${query.toString()}`,
    { signal },
  );

  if (response.success === false) {
    throw new Error(response.message?.trim() || "Não foi possível buscar clientes.");
  }

  const data = response.data ?? {};
  return {
    items: (data.items ?? []).map(normalizeCustomer),
    page: data.page ?? params.page ?? 1,
    pageSize: data.page_size ?? params.pageSize ?? 20,
    total: data.total ?? 0,
    totalPages: data.total_pages ?? 0,
  };
}
