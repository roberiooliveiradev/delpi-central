import type { DeviceDetailTab } from "../types/detail";

export const PRODUCTION_PULSE_BASE_PATH = "/apps/production-pulse";

const DEVICE_DETAIL_TABS: DeviceDetailTab[] = ["overview", "history", "commands"];

export function parseDeviceDetailTab(value: string | null | undefined): DeviceDetailTab {
  if (value && DEVICE_DETAIL_TABS.includes(value as DeviceDetailTab)) {
    return value as DeviceDetailTab;
  }
  return "overview";
}

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
  | { kind: "deviceDetail"; deviceId: string; tab: DeviceDetailTab }
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
    return {
      kind: "deviceDetail",
      deviceId: detailMatch[1],
      tab: parseDeviceDetailTab(query.get("tab")),
    };
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

export function productionPulseDeviceDetailPath(
  deviceId: string,
  tab: DeviceDetailTab = "overview",
): string {
  const query = tab === "overview" ? "" : `?tab=${encodeURIComponent(tab)}`;
  return `${PRODUCTION_PULSE_BASE_PATH}/devices/${deviceId}${query}`;
}
