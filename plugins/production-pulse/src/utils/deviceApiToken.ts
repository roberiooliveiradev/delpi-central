/** Device API token field helpers (cadastro may return plaintext on GET detail). */

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
  /** Token loaded from GET/create response — unchanged value stays «Configurado». */
  baselineToken?: string;
}): DeviceApiTokenFieldStatus {
  const current = input.apiToken.trim();
  const baseline = (input.baselineToken ?? "").trim();
  if (current && current !== baseline) {
    return "pending_save";
  }
  if (input.apiTokenSet || Boolean(baseline)) {
    return "configured";
  }
  return "missing";
}

export function canRevealDeviceApiToken(apiToken: string): boolean {
  return Boolean(apiToken.trim());
}

export function canCopyDeviceApiToken(apiToken: string): boolean {
  return canRevealDeviceApiToken(apiToken);
}

export function ensureDeviceApiTokenForCreate(apiToken: string): string {
  const trimmed = apiToken.trim();
  return trimmed || generateDeviceApiToken();
}
