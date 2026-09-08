import { httpGet, httpPatch, suppliesApiUrl } from "./httpClient";

export type SuppliesPreferences = {
  userId: string;
  defaultBranch: string | null;
  tableDensity: "comfortable" | "compact";
};

export function getPreferences(signal?: AbortSignal): Promise<SuppliesPreferences> {
  return httpGet<SuppliesPreferences>(suppliesApiUrl("/me/preferences"), { signal });
}

export function patchPreferences(
  payload: Partial<Pick<SuppliesPreferences, "defaultBranch" | "tableDensity">>,
  signal?: AbortSignal,
): Promise<SuppliesPreferences> {
  return httpPatch<SuppliesPreferences>(suppliesApiUrl("/me/preferences"), payload, { signal });
}
