import { httpGet, httpPost, httpPut, suppliesApiUrl } from "../../api/httpClient";
import type {
  SupplierCreateDraft,
  SupplierDetail,
  SupplierEditDraft,
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
  const fornecedor: Record<string, string> = {};
  if (draft.supplier_name.trim()) fornecedor.supplier_name = draft.supplier_name.trim();
  if (draft.supplier_short_name.trim())
    fornecedor.supplier_short_name = draft.supplier_short_name.trim();
  if (draft.tax_id.trim()) fornecedor.tax_id = draft.tax_id.trim();
  if (draft.state.trim()) fornecedor.state = draft.state.trim().toUpperCase();
  return httpPost<SupplierWriteResponse>(suppliesApiUrl("/suppliers"), {
    fornecedor,
  }, { signal });
}

export function updateSupplier(
  code: string,
  store: string,
  draft: SupplierEditDraft,
  signal?: AbortSignal,
): Promise<SupplierWriteResponse> {
  const fornecedor: Record<string, string> = {};
  if (draft.supplier_name.trim()) fornecedor.supplier_name = draft.supplier_name.trim();
  if (draft.supplier_short_name.trim())
    fornecedor.supplier_short_name = draft.supplier_short_name.trim();
  return httpPut<SupplierWriteResponse>(
    suppliesApiUrl(supplierPath(code, store)),
    { fornecedor },
    { signal },
  );
}
