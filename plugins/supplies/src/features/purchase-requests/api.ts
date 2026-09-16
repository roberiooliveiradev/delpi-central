import { httpGet, httpGetBlob, suppliesApiUrl } from "../../api/httpClient";
import type {
  PurchaseRequestDetail,
  PurchaseRequestListResponse,
  PurchaseRequestsQuery,
} from "./types";
import { buildListSearchParams } from "./query";

export async function listPurchaseRequests(
  query: PurchaseRequestsQuery,
  signal?: AbortSignal,
): Promise<PurchaseRequestListResponse> {
  const qs = buildListSearchParams(query).toString();
  return httpGet<PurchaseRequestListResponse>(
    suppliesApiUrl(`/purchase-requests?${qs}`),
    { signal },
  );
}

export async function getPurchaseRequest(
  branch: string,
  requestNumber: string,
  filters?: Partial<Pick<PurchaseRequestsQuery, "date_from" | "date_to">>,
  signal?: AbortSignal,
): Promise<PurchaseRequestDetail> {
  const params = new URLSearchParams();
  const dateFrom = filters?.date_from?.trim() ?? "";
  const dateTo = filters?.date_to?.trim() ?? "";
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  const qs = params.toString();
  const path = `/purchase-requests/${encodeURIComponent(branch)}/${encodeURIComponent(requestNumber)}`;
  return httpGet<PurchaseRequestDetail>(
    suppliesApiUrl(qs ? `${path}?${qs}` : path),
    { signal },
  );
}

export async function downloadPurchaseRequestsExport(
  query: PurchaseRequestsQuery,
  signal?: AbortSignal,
): Promise<void> {
  const params = buildListSearchParams(query, { includePagination: false });
  params.set("format", "xlsx");
  const blob = await httpGetBlob(
    suppliesApiUrl(`/purchase-requests/export?${params.toString()}`),
    { signal },
  );
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = "purchase-requests.xlsx";
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}
