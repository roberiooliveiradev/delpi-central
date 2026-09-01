export const PRODUCTION_PULSE_BASE_PATH = "/apps/production-pulse";

export type ProductionPulseRouteKind =
  | "panel"
  | "operator"
  | "deviceNew"
  | "deviceEdit"
  | "deviceDetail"
  | "unknown";

export type ProductionPulseRoute =
  | { kind: "panel" }
  | { kind: "operator" }
  | { kind: "deviceNew"; branch?: string }
  | { kind: "deviceEdit"; deviceId: string }
  | { kind: "deviceDetail"; deviceId: string }
  | { kind: "unknown" };

export function parseProductionPulseRoute(pathname: string, search = ""): ProductionPulseRoute {
  const normalized = pathname.replace(/\/+$/, "") || PRODUCTION_PULSE_BASE_PATH;
  const query = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);

  if (normalized === PRODUCTION_PULSE_BASE_PATH) {
    return { kind: "panel" };
  }

  if (normalized.startsWith(`${PRODUCTION_PULSE_BASE_PATH}/operator`)) {
    return { kind: "operator" };
  }

  if (normalized === `${PRODUCTION_PULSE_BASE_PATH}/devices/new`) {
    return { kind: "deviceNew", branch: query.get("branch") ?? undefined };
  }

  const editMatch = normalized.match(
    new RegExp(`^${PRODUCTION_PULSE_BASE_PATH}/devices/([^/]+)/edit$`),
  );
  if (editMatch) {
    return { kind: "deviceEdit", deviceId: editMatch[1] };
  }

  const detailMatch = normalized.match(
    new RegExp(`^${PRODUCTION_PULSE_BASE_PATH}/devices/([^/]+)$`),
  );
  if (detailMatch) {
    return { kind: "deviceDetail", deviceId: detailMatch[1] };
  }

  return { kind: "unknown" };
}

export function productionPulseDeviceEditPath(deviceId: string): string {
  return `${PRODUCTION_PULSE_BASE_PATH}/devices/${deviceId}/edit`;
}

export function productionPulseDeviceNewPath(branch?: string): string {
  const suffix = branch ? `?branch=${encodeURIComponent(branch)}` : "";
  return `${PRODUCTION_PULSE_BASE_PATH}/devices/new${suffix}`;
}
