import {
  parseKpiNumericValue,
  resolveDelpiKpiTone,
  type DelpiKpiCardTone,
} from "@delpi/plugin-ui/index";

import type { ComunicadoKpiOptions } from "./comunicadoKpiOptions";
import { mergeComunicadoKpiOptions } from "./comunicadoKpiOptions";
import type { ComunicadoDataResolved } from "./comunicadoTypes";
import { isAutoBakedFieldLabel } from "./fieldLabelRegistry";
import { formatCurrency, formatNumber, formatPct } from "./nativeFormat";
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

  const numeric = parseKpiNumericValue(value);

  /**
   * `raw` explícito: se o valor numérico tem excesso de casas (float de API),
   * formata como número — senão o FitText do card fica travado em fonte miúda.
   */
  if (format === "raw") {
    const base = String(value);
    if (numeric != null && /^-?\d+\.\d{4,}$/.test(base.trim())) {
      const text = formatNumber(numeric);
      return unit ? `${text} ${unit}` : text;
    }
    return unit && !base.includes(unit) ? `${base}${unit}` : base;
  }

  if (format == null) {
    if (numeric != null) {
      const text = formatNumber(numeric);
      return unit ? `${text} ${unit}` : text;
    }
    const base = String(value);
    return unit && !base.includes(unit) ? `${base}${unit}` : base;
  }

  if (numeric == null) {
    const base = String(value);
    return unit && !base.includes(unit) ? `${base}${unit}` : base;
  }

  if (format === "percent") {
    const text = formatPct(numeric);
    return unit && unit !== "%" ? `${text} ${unit}` : text;
  }

  if (format === "currency") {
    const text = formatCurrency(numeric);
    return unit && !text.includes(unit) ? `${text} ${unit}` : text;
  }

  if (format === "compact") {
    const text = numeric.toLocaleString("pt-BR", {
      notation: "compact",
      maximumFractionDigits: 1,
    });
    return unit ? `${text} ${unit}` : text;
  }

  const text = formatNumber(numeric);
  return unit ? `${text} ${unit}` : text;
}
