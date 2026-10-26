import { httpGet, httpPost, httpPut, suppliesApiUrl } from "../../api/httpClient";
import { buildCreateFornecedor, buildUpdateFornecedor } from "./query";
import type {
  SupplierCreateDraft,
  SupplierDetail,
  SupplierEditDraft,
  SupplierIntegrationStatus,
  SupplierListEnvelope,
  SupplierWriteResponse,
  SuppliersQuery,
} from "./types";

function supplierPath(code: string, store: string): string {
  return `/suppliers/${encodeURIComponent(code)}/${encodeURIComponent(store)}`;
}

export function listSuppliers(
  query: SuppliersQuery,
  signal?: AbortSignal,
): Promise<SupplierListEnvelope> {
  const params = new URLSearchParams();
  if (query.query.trim()) params.set("query", query.query.trim());
  if (query.state.trim()) params.set("state", query.state.trim());
  if (query.blocked === "0" || query.blocked === "1") {
    params.set("blocked", query.blocked);
  }
  params.set("page", String(query.page));
  params.set("page_size", String(query.page_size));
  return httpGet<SupplierListEnvelope>(
    suppliesApiUrl(`/suppliers?${params.toString()}`),
    { signal },
  );
}

export function getSupplier(
  code: string,
  store: string,
  signal?: AbortSignal,
): Promise<SupplierDetail> {
  return httpGet<SupplierDetail>(suppliesApiUrl(supplierPath(code, store)), {
    signal,
  });
}

export function createSupplier(
  draft: SupplierCreateDraft,
  signal?: AbortSignal,
): Promise<SupplierWriteResponse> {
  return httpPost<SupplierWriteResponse>(suppliesApiUrl("/suppliers"), {
    fornecedor: buildCreateFornecedor(draft),
  }, { signal });
}

/** PUT parcial — somente os campos alterados (`changes` vem do diff revisado). */
export function updateSupplier(
  code: string,
  store: string,
  changes: ReadonlyArray<{ field: keyof SupplierEditDraft; after: string }>,
  signal?: AbortSignal,
): Promise<SupplierWriteResponse> {
  return httpPut<SupplierWriteResponse>(
    suppliesApiUrl(supplierPath(code, store)),
    { fornecedor: buildUpdateFornecedor(changes) },
    { signal },
  );
}

export function getSuppliersIntegrationStatus(
  signal?: AbortSignal,
): Promise<SupplierIntegrationStatus> {
  return httpGet<SupplierIntegrationStatus>(
    suppliesApiUrl("/suppliers/integration-status"),
    { signal },
  );
}
