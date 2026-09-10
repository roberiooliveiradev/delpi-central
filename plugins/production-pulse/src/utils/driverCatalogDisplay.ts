import type { DriverListItem, DriverProtocolKind } from "../api/productionPulseApi";

export type DriverProtocolDisplay = {
  kind: string;
  label: string;
  shortLabel: string;
};

const PROTOCOL_LABELS: Record<
  DriverProtocolKind,
  { label: string; shortLabel: string }
> = {
  http_counter: { label: "Contador HTTP", shortLabel: "Contador" },
  http_gauge: { label: "Sensores HTTP", shortLabel: "Sensores" },
};

export function resolveDriverProtocolDisplay(
  protocolKind: string | null | undefined,
): DriverProtocolDisplay {
  const kind = (protocolKind || "").trim() || "unknown";
  const known = PROTOCOL_LABELS[kind as DriverProtocolKind];
  if (known) {
    return { kind, label: known.label, shortLabel: known.shortLabel };
  }
  return { kind, label: kind, shortLabel: kind };
}

export function summarizeDriverCatalogItem(driver: DriverListItem): {
  protocol: DriverProtocolDisplay;
  metricCount: number;
  commandCount: number;
  archived: boolean;
  eligible: boolean;
} {
  return {
    protocol: resolveDriverProtocolDisplay(driver.protocolKind),
    metricCount: Array.isArray(driver.metrics) ? driver.metrics.length : 0,
    commandCount: Array.isArray(driver.commands) ? driver.commands.length : 0,
    archived: Boolean(driver.archivedAt),
    eligible: Boolean(driver.operatorEligible),
  };
}
