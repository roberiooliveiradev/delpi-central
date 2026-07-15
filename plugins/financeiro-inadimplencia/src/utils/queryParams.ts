import type {
  ClientesQueryParams,
  MensalQueryParams,
  PeriodFilter,
  TitulosQueryParams,
} from "../types/inadimplencia";

function appendPeriodParams(params: URLSearchParams, filters: PeriodFilter): void {
  if (filters.startDate && filters.endDate) {
    params.set("start_date", filters.startDate);
    params.set("end_date", filters.endDate);
  }
}

export function buildPeriodQuery(filters: PeriodFilter): URLSearchParams {
  const params = new URLSearchParams();
  appendPeriodParams(params, filters);
  return params;
}

export function buildMensalQuery(input: MensalQueryParams): URLSearchParams {
  const params = buildPeriodQuery(input);
  if (input.customers?.length) {
    params.set("customers", input.customers.join(","));
  } else {
    if (input.customerCode) params.set("customer_code", input.customerCode);
    if (input.storeCode) params.set("store_code", input.storeCode);
  }
  if (input.novosNegocios) {
    params.set("novos_negocios", "true");
  }
  return params;
}

export function buildClientesQuery(input: ClientesQueryParams): URLSearchParams {
  const params = buildPeriodQuery(input);
  params.set("page", String(input.page ?? 1));
  params.set("page_size", String(input.pageSize ?? 20));
  params.set("sort_by", input.sortBy ?? "late_amount");
  params.set("sort_dir", input.sortDir ?? "desc");
  params.set("only_with_delays", String(input.onlyWithDelays ?? true));
  if (input.q?.trim()) {
    params.set("q", input.q.trim());
  }
  return params;
}

export function buildTitulosQuery(input: TitulosQueryParams): URLSearchParams {
  const params = buildPeriodQuery(input);
  if (input.customerCode) params.set("customer_code", input.customerCode);
  if (input.storeCode) params.set("store_code", input.storeCode);
  if (input.status) params.set("status", input.status);
  if (input.delayRange) params.set("delay_range", input.delayRange);
  if (input.q?.trim()) params.set("q", input.q.trim());
  params.set("page", String(input.page ?? 1));
  params.set("page_size", String(input.pageSize ?? 20));
  params.set("sort_by", input.sortBy ?? "payment_date");
  params.set("sort_dir", input.sortDir ?? "desc");
  return params;
}

export function queryString(params: URLSearchParams): string {
  const value = params.toString();
  return value ? `?${value}` : "";
}
