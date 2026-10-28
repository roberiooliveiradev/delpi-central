/** Comex configurable analysis API client (PROC-0076.COMEX.S2–S4).

Protheus product catalog proxy (via the BFF), NCM homologation
governance and personal saved views — all BFF routes under
``/market-intelligence/comex/*``. The MFE never calls the ERP or the
MDIC source directly.
*/

import {
  httpDelete,
  httpGet,
  httpPost,
  httpPut,
  suppliesApiUrl,
} from "../../api/httpClient";

export type ComexProductType = "MP" | "PI" | "PA";

export type ComexProductItem = {
  code: string;
  description: string;
  type: string;
  group_code: string;
  subgroup: string;
  unit: string;
  ncm_code: string | null;
  ncm_status: "missing" | "malformed" | "present";
  active: string;
  blocked: string;
};

export type ComexProductSearchResponse = {
  items: ComexProductItem[];
  total: number;
  page?: number;
  page_size?: number;
};

export type ComexNcmStatus =
  | "candidate"
  | "pending_fiscal_review"
  | "approved"
  | "rejected"
  | "inactive";

export type ComexNcmGovernance = {
  governance_id: string;
  ncm_code: string;
  ncm_version: string | null;
  description: string | null;
  family_code: string | null;
  product_codes: string[];
  status: ComexNcmStatus;
  notes: string | null;
  requested_by: string;
  requested_at: string;
  decided_by: string | null;
  decided_at: string | null;
  decision_notes: string | null;
  revision: number;
  allowlist_sync?: "synced" | "failed" | "not_applicable";
  /** Present on create when the NCM was already in the shared
   * catalog — the returned record is the existing row (S7
   * idempotent add). */
  already_registered?: boolean;
  events?: ComexNcmGovernanceEvent[];
};

export type ComexNcmGovernanceEvent = {
  event_id: string;
  event_type: string;
  actor_subject: string | null;
  from_status: string | null;
  to_status: string | null;
  notes: string | null;
  created_at: string;
};

export type ComexSavedView = {
  view_id: string;
  owner_user_id: string;
  unit_scope: string | null;
  name: string;
  selected_product_codes: string[];
  selected_materials: string[];
  approved_ncm_references: string[];
  selected_metrics: string[];
  date_range: { date_from: string; date_to: string } | null;
  granularity: "month" | "year";
  view_mode: "chart" | "table";
  created_at: string;
  updated_at: string;
};

export type ComexViewPayload = {
  name: string;
  unit_scope?: string | null;
  selected_product_codes?: string[];
  selected_materials?: string[];
  approved_ncm_references?: string[];
  selected_metrics?: string[];
  date_range?: { date_from: string; date_to: string } | null;
  granularity?: "month" | "year";
  view_mode?: "chart" | "table";
};

function toQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function searchComexProducts(
  params: {
    code?: string;
    description?: string;
    product_type?: string;
    group_code?: string;
    subgroup?: string;
    page?: number;
    page_size?: number;
  },
  signal?: AbortSignal,
): Promise<ComexProductSearchResponse> {
  return httpGet(
    suppliesApiUrl(
      `/market-intelligence/comex/products/search${toQuery(params)}`,
    ),
    { signal },
  );
}

export function listComexNcmGovernance(
  params?: { status?: ComexNcmStatus },
  signal?: AbortSignal,
): Promise<{ items: ComexNcmGovernance[] }> {
  return httpGet(
    suppliesApiUrl(
      `/market-intelligence/comex/ncm-governance${toQuery({
        status: params?.status,
      })}`,
    ),
    { signal },
  );
}

export function createComexNcmRequest(
  body: {
    ncm_code: string;
    description?: string;
    ncm_version?: string;
    family_code?: string;
    product_codes?: string[];
    notes?: string;
    initial_status?: "candidate" | "pending_fiscal_review";
  },
  signal?: AbortSignal,
): Promise<ComexNcmGovernance> {
  return httpPost(
    suppliesApiUrl("/market-intelligence/comex/ncm-governance"),
    body,
    { signal },
  );
}

export function transitionComexNcm(
  governanceId: string,
  body: {
    to_status: ComexNcmStatus;
    notes?: string;
    expected_revision?: number;
  },
  signal?: AbortSignal,
): Promise<ComexNcmGovernance> {
  return httpPost(
    suppliesApiUrl(
      `/market-intelligence/comex/ncm-governance/${governanceId}/transition`,
    ),
    body,
    { signal },
  );
}

export function listComexViews(
  signal?: AbortSignal,
): Promise<{ items: ComexSavedView[] }> {
  return httpGet(suppliesApiUrl("/market-intelligence/comex/views"), {
    signal,
  });
}

export function createComexView(
  body: ComexViewPayload,
  signal?: AbortSignal,
): Promise<ComexSavedView> {
  return httpPost(
    suppliesApiUrl("/market-intelligence/comex/views"),
    body,
    { signal },
  );
}

export function updateComexView(
  viewId: string,
  body: ComexViewPayload,
  signal?: AbortSignal,
): Promise<ComexSavedView> {
  return httpPut(
    suppliesApiUrl(`/market-intelligence/comex/views/${viewId}`),
    body,
    { signal },
  );
}

export function deleteComexView(
  viewId: string,
  signal?: AbortSignal,
): Promise<void> {
  return httpDelete(
    suppliesApiUrl(`/market-intelligence/comex/views/${viewId}`),
    { signal },
  );
}
