import { httpGet, httpPatch, httpPost } from "./httpClient";
import type {
  CreateRequestPayload,
  InvoicePostingComment,
  InvoicePostingDetail,
  InvoicePostingListResponse,
  InvoicePostingRequest,
  ListFilters,
  Supplier,
  UpdateRequestPayload,
} from "../../domain/types";

const API_BASE = "/apps/api-delpi/lancamento-notas-fiscais";

function toQuery(filters: ListFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    params.set(key, String(value));
  });
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export async function searchSuppliers(
  query: string,
  limit = 20,
  signal?: AbortSignal,
): Promise<Supplier[]> {
  const qs = new URLSearchParams({
    query,
    limit: String(limit),
  });
  const data = await httpGet<{ items: Supplier[] }>(
    `${API_BASE}/suppliers?${qs.toString()}`,
    { signal },
  );
  return data.items ?? [];
}

export async function listRequests(
  filters: ListFilters,
  signal?: AbortSignal,
): Promise<InvoicePostingListResponse> {
  return httpGet<InvoicePostingListResponse>(
    `${API_BASE}/requests${toQuery(filters)}`,
    { signal },
  );
}

export async function getRequest(
  requestId: string,
  signal?: AbortSignal,
): Promise<InvoicePostingDetail> {
  return httpGet<InvoicePostingDetail>(`${API_BASE}/requests/${requestId}`, {
    signal,
  });
}

export async function createRequest(
  payload: CreateRequestPayload,
): Promise<InvoicePostingRequest> {
  return httpPost<InvoicePostingRequest>(`${API_BASE}/requests`, payload);
}

export async function updateRequest(
  requestId: string,
  payload: UpdateRequestPayload,
): Promise<InvoicePostingRequest> {
  return httpPatch<InvoicePostingRequest>(
    `${API_BASE}/requests/${requestId}`,
    payload,
  );
}

export async function startRequest(
  requestId: string,
): Promise<InvoicePostingRequest> {
  return httpPost<InvoicePostingRequest>(
    `${API_BASE}/requests/${requestId}/start`,
    {},
  );
}

export async function blockRequest(
  requestId: string,
  body: { block_reason: string; block_description: string },
): Promise<InvoicePostingRequest> {
  return httpPost<InvoicePostingRequest>(
    `${API_BASE}/requests/${requestId}/block`,
    body,
  );
}

export async function resumeRequest(
  requestId: string,
): Promise<InvoicePostingRequest> {
  return httpPost<InvoicePostingRequest>(
    `${API_BASE}/requests/${requestId}/resume`,
    {},
  );
}

export async function cancelRequest(
  requestId: string,
  justification: string,
): Promise<InvoicePostingRequest> {
  return httpPost<InvoicePostingRequest>(
    `${API_BASE}/requests/${requestId}/cancel`,
    { justification },
  );
}

export async function postManualRequest(
  requestId: string,
): Promise<InvoicePostingRequest> {
  return httpPost<InvoicePostingRequest>(
    `${API_BASE}/requests/${requestId}/post-manual`,
    {},
  );
}

export async function addComment(
  requestId: string,
  body: string,
): Promise<InvoicePostingComment> {
  return httpPost<InvoicePostingComment>(
    `${API_BASE}/requests/${requestId}/comments`,
    { body },
  );
}

export type ReconciliationRefreshResult = {
  status: "completed" | "skipped" | "failed";
  updated: number;
};

export async function refreshReconciliation(
  signal?: AbortSignal,
): Promise<ReconciliationRefreshResult> {
  return httpPost<ReconciliationRefreshResult>(
    `${API_BASE}/reconciliation/refresh`,
    {},
    { signal },
  );
}
