import {
  parseKpiNumericValue,
  resolveDelpiKpiTone,
  type DelpiKpiCardTone,
} from "@delpi/plugin-ui/index";

import type { ComunicadoKpiOptions } from "./comunicadoKpiOptions";
import { mergeComunicadoKpiOptions } from "./comunicadoKpiOptions";
import type { ComunicadoDataResolved } from "./comunicadoTypes";
import { isAutoBakedFieldLabel } from "./fieldLabelRegistry";
import type { KpiMetricProjection } from "./viewProjection";

export type KpiViewPresentation = {
  label: string;
  valueText: string;
  hint?: string;
  tone: DelpiKpiCardTone;
  valueColor?: string;
  backgroundColor?: string;
  iconName?: string;
  showIcon: boolean;
};

export type KpiMetricPresentationOverrides = Pick<
  KpiMetricProjection,
  "format" | "colorRules" | "label" | "field"
>;

export function resolveKpiViewPresentation(
  resolved: ComunicadoDataResolved | undefined,
  kpiOptions?: ComunicadoKpiOptions | null,
  metricOverrides?: KpiMetricPresentationOverrides | null,
): KpiViewPresentation {
  const options = mergeComunicadoKpiOptions(kpiOptions);
  const rawValue = resolved?.kpi?.value;
  const numeric = parseKpiNumericValue(rawValue);
  const colorRules = metricOverrides?.colorRules ?? options.colorRules;
  const toneResult = resolveDelpiKpiTone(numeric, colorRules, options.tone ?? "default");
  const valueFormat = metricOverrides?.format ?? options.valueFormat;

  const fieldKey =
    metricOverrides?.field?.trim() ||
    resolved?.kpiMetrics?.[0]?.field?.trim() ||
    "";
  const projectionLabel = metricOverrides?.label;
  const meaningfulProjection =
    typeof projectionLabel === "string" &&
    projectionLabel.trim() &&
    (!fieldKey || !isAutoBakedFieldLabel(projectionLabel, fieldKey));

  const label =
    (meaningfulProjection ? projectionLabel : undefined) ||
    options.title?.trim() ||
    resolved?.kpi?.label ||
    resolved?.label ||
    "Indicador";

  const valueText = formatKpiValue(rawValue, valueFormat, options.unit);
  const hint = options.subtitle?.trim() || undefined;

  return {
    label,
    valueText,
    hint,
    tone: toneResult.tone,
    valueColor: toneResult.valueColor ?? options.valueColor,
    backgroundColor: toneResult.backgroundColor ?? options.backgroundColor,
    iconName:
      options.iconName?.trim() ||
      (options.showIcon !== false ? "Gauge" : undefined),
    showIcon: options.showIcon !== false,
  };
}

function formatKpiValue(
  value: unknown,
  format: ComunicadoKpiOptions["valueFormat"],
  unit?: string,
): string {
  if (value == null || value === "") return "—";
  if (format === "raw" || format == null) {
    const base = String(value);
    return unit && !base.includes(unit) ? `${base}${unit}` : base;
  }

  const numeric = parseKpiNumericValue(value);
  if (numeric == null) {
    const base = String(value);
    return unit && !base.includes(unit) ? `${base}${unit}` : base;
  }

  if (format === "percent") {
    const text = `${numeric.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
    return unit && unit !== "%" ? `${text} ${unit}` : text;
  }

  if (format === "compact") {
    const text = numeric.toLocaleString("pt-BR", {
      notation: "compact",
      maximumFractionDigits: 1,
    });
    return unit ? `${text} ${unit}` : text;
  }

  const text = numeric.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  return unit ? `${text} ${unit}` : text;
}
