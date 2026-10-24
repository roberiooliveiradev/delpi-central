import { httpGet, httpGetBlob, httpPatch, suppliesApiUrl } from "./httpClient";
import type { SuppliesCapabilityFlags } from "./capabilities";
import type { SuppliesPreferences } from "./preferences";
import type { PurchaseRequestListItem } from "../features/purchase-requests/types";

export type SuppliesUserProfile = {
  userId: string;
  name: string;
  email: string;
  jobTitle?: string | null;
  phone?: string | null;
  mobile?: string | null;
  whatsapp?: string | null;
  hasPhoto?: boolean;
  isSelf: boolean;
  preferences: Pick<SuppliesPreferences, "userId" | "defaultBranch" | "tableDensity">;
  capabilities: SuppliesCapabilityFlags | null;
  allowedUnits: string[];
  isSuperadmin?: boolean | null;
  permissions?: string[] | null;
};

export type PatchSuppliesUserProfilePayload = {
  preferences?: Partial<Pick<SuppliesPreferences, "defaultBranch" | "tableDensity">>;
};

export function getUserProfile(
  userId: string,
  signal?: AbortSignal,
): Promise<SuppliesUserProfile> {
  return httpGet<SuppliesUserProfile>(
    suppliesApiUrl(`/users/${encodeURIComponent(userId)}/profile`),
    { signal },
  );
}

export function patchUserProfile(
  userId: string,
  payload: PatchSuppliesUserProfilePayload,
  signal?: AbortSignal,
): Promise<SuppliesUserProfile> {
  return httpPatch<SuppliesUserProfile>(
    suppliesApiUrl(`/users/${encodeURIComponent(userId)}/profile`),
    payload,
    { signal },
  );
}

export type UserRelatedRequestsResponse = {
  items: PurchaseRequestListItem[];
  total: number;
  page: number;
  page_size: number;
  protheus_user_ids: string[];
  requester_unmapped?: boolean;
  /** Explicit history floor applied by the BFF (empty => list default). */
  date_from?: string;
  /** Degradation marker — distinct from an honestly empty universe. */
  error?: string;
};

export function getUserRelatedRequests(
  userId: string,
  options?: { page?: number; pageSize?: number; branches?: string[] },
  signal?: AbortSignal,
): Promise<UserRelatedRequestsResponse> {
  const params = new URLSearchParams();
  for (const branch of options?.branches ?? []) {
    if (branch.trim()) params.append("branch", branch.trim());
  }
  if (options?.page) params.set("page", String(options.page));
  if (options?.pageSize) params.set("page_size", String(options.pageSize));
  const qs = params.toString();
  return httpGet<UserRelatedRequestsResponse>(
    suppliesApiUrl(
      `/users/${encodeURIComponent(userId)}/related-requests${qs ? `?${qs}` : ""}`,
    ),
    { signal },
  );
}

export function getUserPhotoBlob(
  userId: string,
  signal?: AbortSignal,
): Promise<Blob> {
  return httpGetBlob(
    suppliesApiUrl(`/users/${encodeURIComponent(userId)}/photo`),
    { signal },
  );
}
