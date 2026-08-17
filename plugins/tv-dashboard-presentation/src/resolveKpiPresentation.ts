import {
  formatDisplayValue,
  parseKpiNumericValue,
  resolveDelpiKpiTone,
  resolveDisplayFormatSpec,
  specFromKpiValueFormat,
  type DelpiKpiCardTone,
  type DelpiKpiComparisonTone,
  type DisplayFormatSpec,
} from "@delpi/plugin-ui/index";

import type { ComunicadoKpiOptions } from "./comunicadoKpiOptions";
import { mergeComunicadoKpiOptions } from "./comunicadoKpiOptions";
import type { ComunicadoDataResolved } from "./comunicadoTypes";
import { isAutoBakedFieldLabel } from "./fieldLabelRegistry";
import { formatNumber } from "./nativeFormat";
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
  comparisonText?: string;
  comparisonTone?: DelpiKpiComparisonTone;
  progressPct?: number | null;
  sparklinePoints?: number[];
};

export type KpiMetricPresentationOverrides = Pick<
  KpiMetricProjection,
  | "format"
  | "displayFormat"
  | "decimalPlaces"
  | "colorRules"
  | "label"
  | "field"
  | "target"
  | "comparisonMode"
  | "higherIsBetter"
>;

function sparklinePointsFromResolved(resolved: ComunicadoDataResolved | undefined): number[] {
  const series = resolved?.chart?.series?.[0]?.points ?? resolved?.chart?.points ?? [];
  return series
    .map((point) => parseKpiNumericValue(point?.value))
    .filter((n): n is number => n != null && Number.isFinite(n));
}

function formatSignedPct(pct: number): string {
  const abs = Math.abs(pct);
  const text = formatDisplayValue(abs, {
    category: "percent",
    presetId: "percent",
    decimalPlaces: abs >= 10 ? 1 : 2,
  });
  if (pct > 0) return `+${text}`;
  if (pct < 0) return `−${text}`;
  return text;
}

function resolveComparisonPresentation(params: {
  numeric: number | null;
  options: ComunicadoKpiOptions;
  metricOverrides?: KpiMetricPresentationOverrides | null;
  sparklinePoints: number[];
}): {
  comparisonText?: string;
  comparisonTone?: DelpiKpiComparisonTone;
  progressPct?: number | null;
} {
  const mode =
    params.metricOverrides?.comparisonMode ?? params.options.comparisonMode ?? "none";
  const target = params.metricOverrides?.target ?? params.options.target;
  const higherIsBetter =
    params.metricOverrides?.higherIsBetter ?? params.options.higherIsBetter ?? true;
  const showComparison = params.options.showComparison === true;
  const showProgress = params.options.showProgress === true;

  let baseline: number | null = null;
  let vsLabel = "vs período";
  if (mode === "target" && target != null && Number.isFinite(target)) {
    baseline = target;
    vsLabel = "vs meta";
  } else if (mode === "previous" && params.sparklinePoints.length >= 2) {
    baseline = params.sparklinePoints[params.sparklinePoints.length - 2] ?? null;
    vsLabel = "vs período";
  }

  let comparisonText: string | undefined;
  let comparisonTone: DelpiKpiComparisonTone | undefined;
  if (showComparison && params.numeric != null && baseline != null && baseline !== 0) {
    const deltaPct = ((params.numeric - baseline) / Math.abs(baseline)) * 100;
    const favorable = higherIsBetter ? deltaPct >= 0 : deltaPct <= 0;
    const arrow = deltaPct > 0 ? "▲" : deltaPct < 0 ? "▼" : "●";
    comparisonText =
      params.options.comparisonLabel?.trim() ||
      `${arrow} ${formatSignedPct(deltaPct)} ${vsLabel}`;
    comparisonTone =
      Math.abs(deltaPct) < 0.05 ? "neutral" : favorable ? "positive" : "negative";
  } else if (showComparison && params.options.comparisonLabel?.trim()) {
    comparisonText = params.options.comparisonLabel.trim();
    comparisonTone = "neutral";
  }

  let progressPct: number | null = null;
  if (showProgress && params.numeric != null && target != null && Number.isFinite(target) && target !== 0) {
    progressPct = (params.numeric / target) * 100;
  }

  return { comparisonText, comparisonTone, progressPct };
}

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
  const decimalPlaces =
    metricOverrides?.decimalPlaces ?? options.decimalPlaces;

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

  const valueText = formatKpiValue(
    rawValue,
    valueFormat,
    options.unit,
    decimalPlaces,
    metricOverrides?.displayFormat ?? options.displayValueFormat,
  );
  const hint = options.subtitle?.trim() || undefined;
  const sparklinePoints = sparklinePointsFromResolved(resolved);
  const comparison = resolveComparisonPresentation({
    numeric,
    options,
    metricOverrides,
    sparklinePoints,
  });

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
    comparisonText: comparison.comparisonText,
    comparisonTone: comparison.comparisonTone,
    progressPct: comparison.progressPct,
    sparklinePoints: options.showSparkline ? sparklinePoints : undefined,
  };
}

function formatKpiValue(
  value: unknown,
  format: ComunicadoKpiOptions["valueFormat"],
  unit?: string,
  decimalPlaces?: number | null,
  spec?: DisplayFormatSpec | null,
): string {
  if (value == null || value === "") return "—";

  const numeric = parseKpiNumericValue(value);
  const resolved = resolveDisplayFormatSpec(spec, specFromKpiValueFormat(format, decimalPlaces));

  /**
   * `raw` explícito: se o valor numérico tem excesso de casas (float de API),
   * formata como número — senão o FitText do card fica travado em fonte miúda.
   */
  if (resolved.category === "text" && (format === "raw" || format == null)) {
    const base = String(value);
    if (numeric != null && /^-?\d+\.\d{4,}$/.test(base.trim())) {
      const text = formatNumber(numeric, decimalPlaces);
      return unit ? `${text} ${unit}` : text;
    }
    return unit && !base.includes(unit) ? `${base}${unit}` : base;
  }

  if (numeric == null) {
    const base = String(value);
    return unit && !base.includes(unit) ? `${base}${unit}` : base;
  }

  const text = formatDisplayValue(numeric, resolved);
  if (
    unit &&
    resolved.category !== "percent" &&
    resolved.category !== "currency" &&
    !text.includes(unit)
  ) {
    return `${text} ${unit}`;
  }
  if (unit && resolved.category === "percent" && unit !== "%" && !text.includes(unit)) {
    return `${text} ${unit}`;
  }
  return text;
}
