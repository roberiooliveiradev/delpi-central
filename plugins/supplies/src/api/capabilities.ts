import { httpGet, suppliesApiUrl } from "./httpClient";

export type SuppliesCapabilityFlags = {
  portal: boolean;
  purchaseRequests: boolean;
  operations: boolean;
  analytics: boolean;
  administration: boolean;
  viewAll: boolean;
  export: boolean;
};

export type SuppliesCapabilitiesResponse = {
  userId: string;
  capabilities: SuppliesCapabilityFlags;
  allowedUnits: string[];
  aliasesDoNotGrantAppAccess: boolean;
};

export function getCapabilities(signal?: AbortSignal): Promise<SuppliesCapabilitiesResponse> {
  return httpGet<SuppliesCapabilitiesResponse>(suppliesApiUrl("/me/capabilities"), { signal });
}
