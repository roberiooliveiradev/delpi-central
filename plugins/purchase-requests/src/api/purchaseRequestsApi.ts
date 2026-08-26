import type {
  Envelope,
  PurchaseRequestDetail,
  PurchaseRequestListResponse,
  PurchaseRequestRequesterOption,
  PurchaseRequestsQuery,
} from "../types/purchaseRequests";
import { buildListSearchParams } from "../utils/queryParams";
import { httpGet } from "./httpClient";

export const API_BASE = "/apps/purchase-requests-api";

export function unwrapEnvelope<T>(body: Envelope<T>): T {
  if (!body.success) {
    throw new Error(body.message || "Erro na API de solicitações de compra.");
  }
  return body.data;
}

function unwrap<T>(body: Envelope<T>): T {
  return unwrapEnvelope(body);
}

export async function listPurchaseRequests(
  query: PurchaseRequestsQuery,
  options?: { signal?: AbortSignal },
): Promise<PurchaseRequestListResponse> {
  const search = buildListSearchParams(query).toString();
  const url = `${API_BASE}/purchase-requests?${search}`;
  const body = await httpGet<Envelope<PurchaseRequestListResponse>>(url, options);
  return unwrap(body);
}

export type RequesterFacetQuery = Pick<
  PurchaseRequestsQuery,
  | "branch"
  | "date_from"
  | "date_to"
  | "request_number"
  | "cost_center"
  | "product_code"
  | "supplier_code"
  | "order_number"
>;

export async function listPurchaseRequestRequesters(
  query: RequesterFacetQuery,
  options?: { signal?: AbortSignal },
): Promise<PurchaseRequestRequesterOption[]> {
  const params = buildListSearchParams({
    ...query,
    requester_user_ids: [],
    overall_stage: "",
    page: 1,
    page_size: 1,
  });
  params.delete("page");
  params.delete("page_size");
  params.delete("overall_stage");
  const search = params.toString();
  const url = `${API_BASE}/purchase-requests/requesters?${search}`;
  const body = await httpGet<Envelope<{ items: PurchaseRequestRequesterOption[] }>>(url, options);
  return unwrap(body).items ?? [];
}

export async function getPurchaseRequest(
  branch: string,
  requestNumber: string,
  filters: Pick<PurchaseRequestsQuery, "date_from" | "date_to" | "cost_center">,
  options?: { signal?: AbortSignal },
): Promise<PurchaseRequestDetail> {
  const params = buildListSearchParams({
    ...filters,
    branch,
    request_number: requestNumber,
    requester_user_ids: [],
    overall_stage: "",
    product_code: "",
    supplier_code: "",
    order_number: "",
    page: 1,
    page_size: 1,
  });
  const detailKeys = ["date_from", "date_to", "cost_center"] as const;
  const searchParams = new URLSearchParams();
  for (const key of detailKeys) {
    const value = params.get(key);
    if (value) searchParams.set(key, value);
  }
  const qs = searchParams.toString();
  const url = `${API_BASE}/purchase-requests/${encodeURIComponent(branch)}/${encodeURIComponent(requestNumber)}${qs ? `?${qs}` : ""}`;
  const body = await httpGet<Envelope<PurchaseRequestDetail>>(url, options);
  return unwrap(body);
}
