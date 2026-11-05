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
  /** Número da meta já formatado pelo enrich. */
  targetText?: string;
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
  | "targetField"
  | "targetAggregation"
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
  /* Prefer limiares já resolvidos pelo enrich (compareField → número). */
  const colorRules =
    Array.isArray(serverPres?.resolvedColorRules) && serverPres.resolvedColorRules.length > 0
      ? serverPres.resolvedColorRules
      : (metricOverrides?.colorRules ?? options.colorRules);
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

  const dynamicTitle =
    typeof serverPres?.titleDisplay === "string" && serverPres.titleDisplay.trim()
      ? serverPres.titleDisplay.trim()
      : undefined;
  const label =
    (meaningfulProjection ? projectionLabel : undefined) ||
    dynamicTitle ||
    options.title?.trim() ||
    resolved?.kpi?.label ||
    resolved?.label ||
    "Indicador";

  const serverDisplayValue = resolved?.kpi?.displayValue;
  // Prefer per-metric kpi.displayValue (multi-card bake) over primary kpiPresentation.
  const valueText =
    typeof serverDisplayValue === "string"
      ? serverDisplayValue
      : typeof serverPres?.valueDisplay === "string"
        ? serverPres.valueDisplay
        : "—";
  const dynamicSubtitle =
    typeof serverPres?.subtitleDisplay === "string" && serverPres.subtitleDisplay.trim()
      ? serverPres.subtitleDisplay.trim()
      : undefined;
  const hint = dynamicSubtitle || options.subtitle?.trim() || undefined;
  const sparklinePoints =
    Array.isArray(serverPres?.sparklinePoints)
      ? serverPres.sparklinePoints
      : sparklinePointsFromResolved(resolved);
  const comparison =
    serverPres != null
      ? {
          // statusLabel vem do backend e só é concatenada — renderer
          // nunca recalcula posição frente à meta (issue #129 / PR-135).
          // Não pinta status stale quando a comparação está desativada
          // e não duplica texto já composto pelo servidor.
          comparisonText:
            [
              serverPres.comparisonDisplay,
              serverPres.showComparison !== false &&
              typeof serverPres.statusLabel === "string" &&
              serverPres.statusLabel.trim() !== "" &&
              !(serverPres.comparisonDisplay ?? "").includes(serverPres.statusLabel)
                ? serverPres.statusLabel
                : undefined,
            ]
              .filter((p): p is string => typeof p === "string" && p.trim() !== "")
              .join(" · ") || undefined,
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
    targetText:
      typeof serverPres?.targetDisplay === "string" && serverPres.targetDisplay.trim()
        ? serverPres.targetDisplay.trim()
        : undefined,
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
