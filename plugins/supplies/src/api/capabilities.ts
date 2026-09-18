import { httpGet, suppliesApiUrl } from "./httpClient";

export type SuppliesCapabilityFlags = {
  access: boolean;
  manage: boolean;
};

export type SuppliesCapabilitiesResponse = {
  userId: string;
  capabilities: SuppliesCapabilityFlags;
  allowedUnits: string[];
};

export function getCapabilities(signal?: AbortSignal): Promise<SuppliesCapabilitiesResponse> {
  return httpGet<SuppliesCapabilitiesResponse>(suppliesApiUrl("/me/capabilities"), { signal });
}
