import { httpGet, httpGetBlob, httpPatch, httpPost } from "./httpClient";
import type {
  CreateRequestPayload,
  InvoicePostingComment,
  InvoicePostingDetail,
  InvoicePostingListResponse,
  InvoicePostingRequest,
  CteDetail,
  ListFilters,
  NfeItemDetail,
  NfseDetail,
  ReceivedInvoiceSearch,
  OpenPurchaseOrdersResponse,
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

export async function listRequestPurchaseOrders(
  requestId: string,
  signal?: AbortSignal,
): Promise<OpenPurchaseOrdersResponse> {
  return httpGet<OpenPurchaseOrdersResponse>(
    `${API_BASE}/requests/${requestId}/purchase-orders`,
    { signal },
  );
}

export async function listOpenPurchaseOrders(
  branch: string,
  supplierCode: string,
  supplierStore: string,
  signal?: AbortSignal,
): Promise<OpenPurchaseOrdersResponse> {
  const params = new URLSearchParams({
    branch,
    supplier_code: supplierCode,
    supplier_store: supplierStore,
  });
  return httpGet<OpenPurchaseOrdersResponse>(
    `${API_BASE}/purchase-orders/open?${params.toString()}`,
    { signal },
  );
}

export async function linkRequestPurchaseOrder(
  requestId: string,
  body:
    | {
        groups: Array<{
          order_number: string;
          delivery_date: string | null;
          lines?: Array<{ order_item: string }>;
        }>;
      }
    | { order_number: string; delivery_date: string | null },
): Promise<InvoicePostingRequest> {
  return httpPost<InvoicePostingRequest>(
    `${API_BASE}/requests/${requestId}/purchase-orders/link`,
    body,
  );
}

export async function searchReceivedInvoices(filters: {
  invoiceNumber?: string;
  supplierCnpj?: string;
  page?: number;
  documentType?: "all" | "nfe" | "nfse" | "cte";
}): Promise<ReceivedInvoiceSearch> {
  const params = new URLSearchParams();
  if (filters.invoiceNumber) params.set("invoice_number", filters.invoiceNumber);
  if (filters.supplierCnpj) params.set("supplier_cnpj", filters.supplierCnpj);
  if (filters.documentType) params.set("document_type", filters.documentType);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", "25");
  return httpGet<ReceivedInvoiceSearch>(`${API_BASE}/received-invoices?${params.toString()}`);
}

export function fetchReceivedNfseDetail(documentId: string, branch: string): Promise<NfseDetail> {
  const params = new URLSearchParams({ branch, document_type: "nfse" });
  return httpGet<NfseDetail>(
    `${API_BASE}/received-invoices/${encodeURIComponent(documentId)}/detail?${params.toString()}`,
  );
}

export function fetchReceivedCteDetail(
  documentId: string,
  fileId: string,
  accessKey: string,
  branch: string,
): Promise<CteDetail> {
  const params = new URLSearchParams({
    branch,
    document_type: "cte",
    file_id: fileId,
    access_key: accessKey,
  });
  return httpGet<CteDetail>(
    `${API_BASE}/received-invoices/${encodeURIComponent(documentId)}/detail?${params.toString()}`,
  );
}

export function fetchReceivedNfeItems(
  documentId: string,
  input: {
    providerEntityId: string;
    accessKey: string;
    branch: string;
    supplierCode: string;
    supplierStore: string;
  },
  signal?: AbortSignal,
): Promise<NfeItemDetail> {
  const params = new URLSearchParams({
    branch: input.branch,
    document_type: "nfe",
    provider_entity_id: input.providerEntityId,
    access_key: input.accessKey,
    supplier_code: input.supplierCode,
    supplier_store: input.supplierStore,
  });
  return httpGet<NfeItemDetail>(
    `${API_BASE}/received-invoices/${encodeURIComponent(documentId)}/detail?${params.toString()}`,
    { signal },
  );
}

export function fetchReceivedCteDacte(
  documentId: string,
  fileId: string,
  accessKey: string,
  branch: string,
): Promise<Blob> {
  const params = new URLSearchParams({
    branch,
    file_id: fileId,
    access_key: accessKey,
  });
  return httpGetBlob(
    `${API_BASE}/received-invoices/${encodeURIComponent(documentId)}/dacte?${params.toString()}`,
  );
}

export function downloadReceivedNfseXml(
  documentId: string,
  variant: "original" | "standard",
  branch: string,
): Promise<Blob> {
  const params = new URLSearchParams({ branch, document_type: "nfse" });
  return httpGetBlob(
    `${API_BASE}/received-invoices/${encodeURIComponent(documentId)}/xml/${variant}?${params.toString()}`,
  );
}

export function fetchRequestFiscalAttachment(
  requestId: string,
  attachmentType: "xml_original" | "xml_standard" | "dacte",
): Promise<Blob> {
  return httpGetBlob(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/fiscal-attachments/${attachmentType}`,
  );
}

export function fetchReceivedInvoicePreview(
  documentId: string,
  accessKey: string,
  branch: string,
): Promise<Blob> {
  const params = new URLSearchParams({ access_key: accessKey, branch });
  return httpGetBlob(`${API_BASE}/received-invoices/${encodeURIComponent(documentId)}/danfe?${params.toString()}`);
}

export function fetchRequestDanfe(requestId: string, disposition: "inline" | "attachment"): Promise<Blob> {
  const params = new URLSearchParams({ disposition });
  return httpGetBlob(`${API_BASE}/requests/${encodeURIComponent(requestId)}/danfe?${params.toString()}`);
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
  body: {
    block_reason: string;
    block_description: string;
    assignee_user_id: string;
    assignee_name: string;
  },
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
  mentionedUserIds: string[] = [],
): Promise<InvoicePostingComment> {
  return httpPost<InvoicePostingComment>(
    `${API_BASE}/requests/${requestId}/comments`,
    {
      body,
      mentioned_user_ids: mentionedUserIds,
    },
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
