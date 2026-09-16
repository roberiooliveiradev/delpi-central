import { httpGet, httpGetBlob, suppliesApiUrl } from "../../api/httpClient";
import type {
  PurchaseOrderDetail,
  PurchaseOrderListResponse,
  PurchaseOrdersQuery,
} from "./types";
import { buildListSearchParams } from "./query";

export async function listPurchaseOrders(
  query: PurchaseOrdersQuery,
  signal?: AbortSignal,
): Promise<PurchaseOrderListResponse> {
  const qs = buildListSearchParams(query).toString();
  return httpGet<PurchaseOrderListResponse>(
    suppliesApiUrl(`/purchase-orders?${qs}`),
    { signal },
  );
}

export async function exportPurchaseOrders(
  query: PurchaseOrdersQuery,
  signal?: AbortSignal,
): Promise<Blob> {
  const qs = buildListSearchParams(query, { includePagination: false }).toString();
  return httpGetBlob(suppliesApiUrl(`/purchase-orders/export?${qs}`), { signal });
}

export async function getPurchaseOrder(
  branch: string,
  orderNumber: string,
  signal?: AbortSignal,
): Promise<PurchaseOrderDetail> {
  const path = `/purchase-orders/${encodeURIComponent(branch)}/${encodeURIComponent(orderNumber)}`;
  return httpGet<PurchaseOrderDetail>(suppliesApiUrl(path), { signal });
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
