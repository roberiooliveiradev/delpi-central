import { httpGet, httpPatch, suppliesApiUrl } from "./httpClient";
import type { SuppliesCapabilityFlags } from "./capabilities";
import type { SuppliesPreferences } from "./preferences";

export type SuppliesUserProfile = {
  userId: string;
  name: string;
  email: string;
  isSelf: boolean;
  preferences: Pick<SuppliesPreferences, "userId" | "defaultBranch" | "tableDensity">;
  capabilities: SuppliesCapabilityFlags | null;
  allowedUnits: string[];
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
