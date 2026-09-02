import { PP_HELP } from "../content/helpTooltips";
import type { DeviceCapabilities } from "../types/device";

export type MetricThresholds = NonNullable<DeviceCapabilities["thresholds"]>[string];

export type MetricThresholdLevel = "normal" | "warn" | "danger";

export function resolveMetricThresholdLevel(
  metricKey: string,
  rawValue: number | string | null | undefined,
  thresholds?: Record<string, MetricThresholds>,
): MetricThresholdLevel {
  if (rawValue === null || rawValue === undefined || rawValue === "") {
    return "normal";
  }
  const numeric = typeof rawValue === "number" ? rawValue : Number(rawValue);
  if (Number.isNaN(numeric)) return "normal";

  const rule = thresholds?.[metricKey];
  if (!rule) return "normal";

  if (rule.dangerAbove !== undefined && numeric >= rule.dangerAbove) return "danger";
  if (rule.warnAbove !== undefined && numeric >= rule.warnAbove) return "warn";
  if (rule.dangerBelow !== undefined && numeric <= rule.dangerBelow) return "danger";
  if (rule.warnBelow !== undefined && numeric <= rule.warnBelow) return "warn";
  return "normal";
}

export function gaugeThresholdAriaLabel(level: MetricThresholdLevel): string | undefined {
  if (level === "warn") return PP_HELP.operator.gaugeThresholdWarn;
  if (level === "danger") return PP_HELP.operator.gaugeThresholdDanger;
  return undefined;
}
