import type { DeviceDetailTab } from "../types/detail";
import type { OperatorAnchorFilter } from "../types/operator";

export const PRODUCTION_PULSE_BASE_PATH = "/apps/production-pulse";
export const PRODUCTION_PULSE_OPERATOR_BASE = `${PRODUCTION_PULSE_BASE_PATH}/operator`;

const DEVICE_DETAIL_TABS: DeviceDetailTab[] = ["overview", "history", "commands"];

const OPERATOR_ANCHOR_FILTERS: OperatorAnchorFilter[] = [
  "",
  "work_center",
  "machine",
  "equipment",
];

export function parseDeviceDetailTab(value: string | null | undefined): DeviceDetailTab {
  if (value && DEVICE_DETAIL_TABS.includes(value as DeviceDetailTab)) {
    return value as DeviceDetailTab;
  }
  return "overview";
}

export function parseOperatorAnchorFilter(
  value: string | null | undefined,
): OperatorAnchorFilter {
  if (value && OPERATOR_ANCHOR_FILTERS.includes(value as OperatorAnchorFilter)) {
    return value as OperatorAnchorFilter;
  }
  return "";
}

export type ProductionPulseRouteKind =
  | "panel"
  | "operatorHub"
  | "operatorPicker"
  | "operatorDevice"
  | "deviceNew"
  | "deviceEdit"
  | "deviceDetail"
  | "unknown";

export type ProductionPulseRoute =
  | { kind: "panel" }
  | { kind: "operatorHub"; branch: string; anchorType: OperatorAnchorFilter; search: string }
  | { kind: "operatorPicker"; placementKey: string; branch: string }
  | { kind: "operatorDevice"; deviceId: string; branch: string; placementKey?: string }
  | { kind: "deviceNew"; branch?: string }
  | { kind: "deviceEdit"; deviceId: string }
  | { kind: "deviceDetail"; deviceId: string; tab: DeviceDetailTab }
  | { kind: "unknown" };

function decodePathSegment(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function parseProductionPulseRoute(pathname: string, search = ""): ProductionPulseRoute {
  const normalized = pathname.replace(/\/+$/, "") || PRODUCTION_PULSE_BASE_PATH;
  const query = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);

  if (normalized === PRODUCTION_PULSE_BASE_PATH) {
    return { kind: "panel" };
  }

  if (normalized === PRODUCTION_PULSE_OPERATOR_BASE) {
    return {
      kind: "operatorHub",
      branch: query.get("branch") ?? "01",
      anchorType: parseOperatorAnchorFilter(query.get("anchorType")),
      search: query.get("search") ?? "",
    };
  }

  const operatorDeviceMatch = normalized.match(
    new RegExp(`^${PRODUCTION_PULSE_OPERATOR_BASE}/devices/([^/]+)$`),
  );
  if (operatorDeviceMatch) {
    return {
      kind: "operatorDevice",
      deviceId: operatorDeviceMatch[1],
      branch: query.get("branch") ?? "01",
      placementKey: query.get("placementKey")
        ? decodePathSegment(query.get("placementKey")!)
        : undefined,
    };
  }

  const operatorPickerMatch = normalized.match(
    new RegExp(`^${PRODUCTION_PULSE_OPERATOR_BASE}/placements/([^/]+)$`),
  );
  if (operatorPickerMatch) {
    return {
      kind: "operatorPicker",
      placementKey: decodePathSegment(operatorPickerMatch[1]),
      branch: query.get("branch") ?? "01",
    };
  }

  if (normalized.startsWith(`${PRODUCTION_PULSE_OPERATOR_BASE}/`)) {
    return { kind: "unknown" };
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

export function productionPulseOperatorPath(
  branch: string,
  filters?: { anchorType?: OperatorAnchorFilter; search?: string },
): string {
  const params = new URLSearchParams({ branch });
  if (filters?.anchorType) params.set("anchorType", filters.anchorType);
  if (filters?.search?.trim()) params.set("search", filters.search.trim());
  return `${PRODUCTION_PULSE_OPERATOR_BASE}?${params}`;
}

export function productionPulseOperatorPlacementPath(
  placementKey: string,
  branch: string,
): string {
  const params = new URLSearchParams({ branch });
  return `${PRODUCTION_PULSE_OPERATOR_BASE}/placements/${encodeURIComponent(placementKey)}?${params}`;
}

export function productionPulseOperatorDevicePath(
  deviceId: string,
  branch: string,
  placementKey?: string,
): string {
  const params = new URLSearchParams({ branch });
  if (placementKey) params.set("placementKey", placementKey);
  return `${PRODUCTION_PULSE_OPERATOR_BASE}/devices/${deviceId}?${params}`;
}
