import { httpGet, httpGetBlob, suppliesApiUrl } from "../../api/httpClient";
import { normalizeSuppliesUnitCode } from "../../app/suppliesUnits";
import type {
  PersonRef,
  PurchaseRequestDetail,
  PurchaseRequestListResponse,
  PurchaseRequestSummary,
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

export async function listPurchaseRequestSummary(
  query: PurchaseRequestsQuery,
  signal?: AbortSignal,
): Promise<PurchaseRequestSummary> {
  const qs = buildListSearchParams(query, {
    includePagination: false,
    includeStages: false,
  }).toString();
  return httpGet<PurchaseRequestSummary>(
    suppliesApiUrl(`/purchase-requests/summary?${qs}`),
    { signal },
  );
}
export type PurchaseRequestRequesterFacet = PersonRef;

export type PurchaseRequestCostCenterFacet = {
  branch?: string | null;
  code?: string | null;
  description?: string | null;
};

export type PurchaseRequestFacetScope = {
  branches: readonly string[];
  date_from: string;
  date_to: string;
};

/** Facet scope = authorized universe under branches + period (no self-filters). */
function buildFacetSearchParams(
  scope: PurchaseRequestFacetScope,
): URLSearchParams {
  const params = new URLSearchParams();
  for (const branch of scope.branches) {
    const code = normalizeSuppliesUnitCode(branch);
    if (code) params.append("branch", code);
  }
  if (scope.date_from.trim()) params.set("date_from", scope.date_from.trim());
  if (scope.date_to.trim()) params.set("date_to", scope.date_to.trim());
  return params;
}

export async function listPurchaseRequestRequesters(
  scope: PurchaseRequestFacetScope,
  signal?: AbortSignal,
): Promise<PurchaseRequestRequesterFacet[]> {
  const qs = buildFacetSearchParams(scope).toString();
  const payload = await httpGet<{ items?: PurchaseRequestRequesterFacet[] }>(
    suppliesApiUrl(`/purchase-requests/requesters?${qs}`),
    { signal },
  );
  return Array.isArray(payload?.items) ? payload.items : [];
}

export async function listPurchaseRequestCostCenters(
  scope: PurchaseRequestFacetScope,
  signal?: AbortSignal,
): Promise<PurchaseRequestCostCenterFacet[]> {
  const qs = buildFacetSearchParams(scope).toString();
  const payload = await httpGet<{ items?: PurchaseRequestCostCenterFacet[] }>(
    suppliesApiUrl(`/purchase-requests/cost-centers?${qs}`),
    { signal },
  );
  return Array.isArray(payload?.items) ? payload.items : [];
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
