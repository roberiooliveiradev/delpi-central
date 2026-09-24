import {
  parseKpiNumericValue,
  resolveDelpiKpiTone,
  type DelpiKpiCardTone,
  type DelpiKpiComparisonTone,
  type KpiLayoutVariant,
} from "@delpi/plugin-ui/index";

import type { ComunicadoKpiOptions } from "./comunicadoKpiOptions";
import { mergeComunicadoKpiOptions } from "./comunicadoKpiOptions";
import type { ComunicadoDataResolved } from "./comunicadoTypes";
import { isAutoBakedFieldLabel } from "./fieldLabelRegistry";
import {
  resolveKpiOptionsWithAutoContext,
  sparklinePointsFromResolved,
} from "./resolveKpiAutoContext";
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
  /** Variante efetiva para o kit (hero|row|scorecard). */
  variant?: KpiLayoutVariant;
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

/**
 * Paint KPI — values/comparison/spark from enrich `kpiPresentation` / `displayValue` only.
 * No client format fallback (FE-BE-002 semantic zero).
 */
export function resolveKpiViewPresentation(
  resolved: ComunicadoDataResolved | undefined,
  kpiOptions?: ComunicadoKpiOptions | null,
  metricOverrides?: KpiMetricPresentationOverrides | null,
): KpiViewPresentation {
  const serverPres = resolved?.kpiPresentation;
  const merged = mergeComunicadoKpiOptions(kpiOptions);
  const options = resolveKpiOptionsWithAutoContext(merged, resolved, metricOverrides);
  const rawValue = resolved?.kpi?.value;
  const numeric = parseKpiNumericValue(rawValue);
  const colorRules = metricOverrides?.colorRules ?? options.colorRules;
  const toneResult = resolveDelpiKpiTone(numeric, colorRules, options.tone ?? "default");

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

  const serverDisplayValue = resolved?.kpi?.displayValue;
  const valueText =
    typeof serverPres?.valueDisplay === "string"
      ? serverPres.valueDisplay
      : typeof serverDisplayValue === "string"
        ? serverDisplayValue
        : "—";
  const hint = options.subtitle?.trim() || undefined;
  const sparklinePoints =
    Array.isArray(serverPres?.sparklinePoints)
      ? serverPres.sparklinePoints
      : sparklinePointsFromResolved(resolved);
  const comparison =
    serverPres != null
      ? {
          comparisonText: serverPres.comparisonDisplay ?? undefined,
          comparisonTone: serverPres.comparisonTone ?? undefined,
          progressPct: serverPres.progressPct ?? null,
        }
      : {
          comparisonText: undefined,
          comparisonTone: undefined,
          progressPct: null,
        };

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
    sparklinePoints:
      serverPres?.showSparkline === false
        ? undefined
        : serverPres?.showSparkline || options.showSparkline
          ? sparklinePoints
          : undefined,
    variant: options.variant,
  };
}
