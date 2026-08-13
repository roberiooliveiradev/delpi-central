import userAccessContent from "./userAccess.json";

const PERMISSION_LABELS = userAccessContent.permissionLabels as Record<string, string>;
const CAPABILITY_LABELS = userAccessContent.capabilityLabels as Record<string, string>;

export const USER_ACCESS_COPY = userAccessContent.copy;

export type AccessPermissionItem = {
  code: string;
  label: string;
};

export type AccessCapabilityItem = {
  key: string;
  label: string;
  granted: boolean;
};

/** Filtra e rotula permissões commercial.* do /me. */
export function listCommercialPermissions(
  permissions: readonly string[] | null | undefined,
): AccessPermissionItem[] {
  const codes = [...new Set((permissions ?? []).map((item) => String(item).trim()).filter(Boolean))]
    .filter((code) => code.startsWith("commercial."))
    .sort((a, b) => a.localeCompare(b, "pt-BR"));
  return codes.map((code) => ({
    code,
    label: PERMISSION_LABELS[code] || code.replace(/^commercial\./, ""),
  }));
}

export function listGrantedCapabilities(
  capabilities: Record<string, boolean> | null | undefined,
): AccessCapabilityItem[] {
  const entries = Object.entries(capabilities ?? {});
  return entries
    .filter(([, granted]) => Boolean(granted))
    .map(([key, granted]) => ({
      key,
      label: CAPABILITY_LABELS[key] || key,
      granted: Boolean(granted),
    }))
    .sort((a, b) => a.label.localeCompare(b.label, "pt-BR"));
}

export function formatPortfoliosCount(count: number): string {
  return USER_ACCESS_COPY.portfoliosCount.replace("{count}", String(count));
}
