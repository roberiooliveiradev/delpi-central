import type { OperatorDeviceItem, OperatorPlacement } from "../types/operator";
import { formatMetricValue, metricLabel, primaryMetricKey } from "./detailDisplay";
import { anchorTypeLabel, roleLabel } from "./deviceDisplay";

export function formatByRoleSummary(byRole: Record<string, number>): string {
  const parts: string[] = [];
  const counter = byRole.pulse_counter ?? 0;
  const gauge = byRole.process_gauge ?? 0;
  const telemetry = byRole.telemetry ?? 0;

  if (counter > 0) {
    parts.push(`${counter} cont${counter > 1 ? "s" : ""}`);
  }
  const sensors = gauge + telemetry;
  if (sensors > 0) {
    parts.push(`${sensors} sens${sensors > 1 ? "" : ""}`);
  }
  if (parts.length === 0) {
    return "Sem devices";
  }
  return parts.join(" · ");
}

export function formatPlacementMeta(placement: OperatorPlacement): string {
  const roleSummary = formatByRoleSummary(placement.byRole);
  const online =
    placement.onlineCount > 0
      ? `${placement.onlineCount} online`
      : placement.deviceCount > 0
        ? "offline"
        : "";
  return [roleSummary, online].filter(Boolean).join(" · ");
}

export function formatPrimaryPreview(placement: OperatorPlacement): string | null {
  const preview = placement.primaryMetricPreview;
  if (!preview?.key) return null;
  return formatMetricValue(preview.key, preview.value);
}

export function operatorRoleBadgeLabel(roleKey: string): string {
  if (roleKey === "pulse_counter") return "Contador";
  if (roleKey === "process_gauge") return "Sensor";
  return roleLabel(roleKey);
}

export function operatorDevicePreview(device: OperatorDeviceItem): string {
  const key = primaryMetricKey(device.lastMetrics, device.capabilities);
  if (!key) return device.online ? "Online" : "Offline";
  return formatMetricValue(key, device.lastMetrics[key]);
}

export function resolveOperatorSurface(device: OperatorDeviceItem): string {
  return device.capabilities?.operatorSurface ?? "gauge_readout";
}

export function placementAnchorBadge(anchorType: string): string {
  return anchorTypeLabel(anchorType);
}

export function metricDisplayLabel(device: OperatorDeviceItem): string {
  const key = primaryMetricKey(device.lastMetrics, device.capabilities);
  return key ? metricLabel(key) : "Métrica";
}

export function operatorPlacementTitle(placement: OperatorPlacement): string {
  const label = placement.placementLabel?.trim();
  if (label) return label;
  if (placement.anchorType === "standalone") {
    return anchorTypeLabel("standalone");
  }
  return "—";
}

export function resolveOperatorHeaderTitle(
  device: OperatorDeviceItem,
  placementLabel?: string,
): string {
  const candidate = placementLabel ?? device.placementLabel;
  if (
    !candidate ||
    /^s:[0-9a-f-]{8,}$/i.test(candidate) ||
    candidate === device.placementKey
  ) {
    return device.name;
  }
  return candidate;
}
