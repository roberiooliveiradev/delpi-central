import { httpGet, httpPatch, httpPost } from "./httpClient";
import type {
  Carrier,
  IssuanceRequest,
  ListFilters,
  OpenSalesOrderGroup,
  Party,
  PartyType,
  ProductHit,
  RequestDetail,
  WarehouseBalance,
} from "../../domain/types";

const API_BASE = "/apps/api-delpi/invoice-issuance";

export async function searchParties(
  partyType: PartyType,
  query: string,
  limit = 20,
  signal?: AbortSignal,
): Promise<Party[]> {
  const qs = new URLSearchParams({
    party_type: partyType,
    query,
    limit: String(limit),
  });
  const data = await httpGet<{ items: Party[] }>(
    `${API_BASE}/parties?${qs.toString()}`,
    { signal },
  );
  return data.items;
}

export async function searchProducts(
  query: string,
  limit = 20,
  signal?: AbortSignal,
): Promise<ProductHit[]> {
  const qs = new URLSearchParams({ query, limit: String(limit) });
  const data = await httpGet<{ items: ProductHit[] }>(
    `${API_BASE}/products?${qs.toString()}`,
    { signal },
  );
  return data.items;
}

export async function getWarehouse01Balance(
  code: string,
  branch: string,
  signal?: AbortSignal,
): Promise<WarehouseBalance> {
  const qs = new URLSearchParams({ branch });
  return httpGet<WarehouseBalance>(
    `${API_BASE}/products/${encodeURIComponent(code)}/warehouse-01-balance?${qs.toString()}`,
    { signal },
  );
}

export async function searchCarriers(
  query: string,
  limit = 20,
  signal?: AbortSignal,
): Promise<Carrier[]> {
  const qs = new URLSearchParams({ query, limit: String(limit) });
  const data = await httpGet<{ items: Carrier[] }>(
    `${API_BASE}/carriers?${qs.toString()}`,
    { signal },
  );
  return data.items;
}

export async function listOpenSalesOrders(
  branch: string,
  partyCode: string,
  partyStore: string,
  signal?: AbortSignal,
): Promise<{
  orders: OpenSalesOrderGroup[];
  orders_count: number;
  lines_count: number;
}> {
  const qs = new URLSearchParams({
    branch,
    party_code: partyCode,
    party_store: partyStore,
  });
  return httpGet(`${API_BASE}/open-sales-orders?${qs.toString()}`, { signal });
}

export type CreateRequestPayload = {
  branch_code: string;
  party_type: PartyType;
  party_code: string;
  party_store: string;
  invoice_type: string;
  invoice_type_other?: string | null;
  freight_mode: string;
  carrier_code?: string | null;
  carrier_name?: string | null;
  weight_kg: number;
  volume_count: number;
  observation?: string | null;
  items: Array<{
    product_code: string;
    product_description: string;
    quantity: number;
    unit_price: number;
    stock_write_off: boolean;
    sales_order?: string | null;
    sales_order_item?: string | null;
    customer_order_number?: string | null;
  }>;
};

export async function createRequest(payload: CreateRequestPayload): Promise<IssuanceRequest> {
  return httpPost<IssuanceRequest>(`${API_BASE}/requests`, payload);
}

export async function listRequests(
  filters: ListFilters,
  signal?: AbortSignal,
): Promise<{ items: IssuanceRequest[]; total: number; page: number; page_size: number; total_pages: number }> {
  const qs = new URLSearchParams({
    branch: filters.branch,
    page: String(filters.page),
    page_size: String(filters.page_size),
  });
  if (filters.status) qs.set("status", filters.status);
  if (filters.invoice_type) qs.set("invoice_type", filters.invoice_type);
  if (filters.q) qs.set("q", filters.q);
  return httpGet(`${API_BASE}/requests?${qs.toString()}`, { signal });
}

export async function getRequest(id: string, signal?: AbortSignal): Promise<RequestDetail> {
  return httpGet<RequestDetail>(`${API_BASE}/requests/${id}`, { signal });
}

export async function updateReturnedRequest(
  id: string,
  payload: CreateRequestPayload,
): Promise<IssuanceRequest> {
  return httpPatch<IssuanceRequest>(`${API_BASE}/requests/${id}`, payload);
}

export async function resubmitRequest(id: string): Promise<IssuanceRequest> {
  return httpPost<IssuanceRequest>(`${API_BASE}/requests/${id}/resubmit`, {});
}

export async function startRequest(id: string): Promise<IssuanceRequest> {
  return httpPost<IssuanceRequest>(`${API_BASE}/requests/${id}/start`, {});
}

export async function returnRequest(id: string, reason: string): Promise<IssuanceRequest> {
  return httpPost<IssuanceRequest>(`${API_BASE}/requests/${id}/return`, { reason });
}

export async function issueRequest(id: string): Promise<IssuanceRequest> {
  return httpPost<IssuanceRequest>(`${API_BASE}/requests/${id}/issue`, {});
}

export async function cancelRequest(
  id: string,
  justification: string,
): Promise<IssuanceRequest> {
  return httpPost<IssuanceRequest>(`${API_BASE}/requests/${id}/cancel`, { justification });
}
