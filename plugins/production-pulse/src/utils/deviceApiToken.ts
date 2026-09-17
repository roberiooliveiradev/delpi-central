/** Client-side device API token helpers (session UX only — API remains canonical). */

export type DeviceApiTokenFieldStatus = "configured" | "missing" | "pending_save";

export function generateDeviceApiToken(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return `tok${Date.now().toString(16)}${Math.random().toString(16).slice(2, 10)}`;
}

export function resolveDeviceApiTokenFieldStatus(input: {
  apiToken: string;
  apiTokenSet: boolean;
}): DeviceApiTokenFieldStatus {
  if (input.apiToken.trim()) {
    return "pending_save";
  }
  if (input.apiTokenSet) {
    return "configured";
  }
  return "missing";
}

export function canCopyDeviceApiToken(apiToken: string): boolean {
  return Boolean(apiToken.trim());
}

export function ensureDeviceApiTokenForCreate(apiToken: string): string {
  const trimmed = apiToken.trim();
  return trimmed || generateDeviceApiToken();
}
