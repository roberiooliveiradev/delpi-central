import { httpGet, suppliesApiUrl } from "../../api/httpClient";
import type { PurchaseOrderListResponse, PurchaseOrdersQuery } from "./types";
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
