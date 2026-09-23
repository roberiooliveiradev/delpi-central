/**
 * Auto-contexto do KPI: liga comparison/sparkline/progress a partir de `resolved`
 * quando `kpiOptions.contextMode === "auto"`.
 *
 * Compatibilidade: `contextMode` omitido ≡ `"off"` (slides legacy inalterados).
 */

import { parseKpiNumericValue, type KpiContextMode, type KpiLayoutVariant } from "@delpi/plugin-ui/index";

import type { ComunicadoKpiOptions } from "./comunicadoKpiOptions";
import type { ComunicadoDataResolved } from "./comunicadoTypes";

type AutoContextMetricOverrides = {
  target?: number;
  comparisonMode?: "none" | "target" | "previous";
  higherIsBetter?: boolean;
};

export function effectiveKpiContextMode(
  options?: ComunicadoKpiOptions | null,
): KpiContextMode {
  const mode = options?.contextMode;
  if (mode === "auto" || mode === "manual" || mode === "off") return mode;
  return "off";
}

export function suggestKpiVariantFromFrame(frame?: {
  h?: number;
} | null): KpiLayoutVariant {
  const h = Number(frame?.h);
  if (Number.isFinite(h) && h < 28) return "row";
  if (Number.isFinite(h) && h >= 40) return "hero";
  return "hero";
}

export function sparklinePointsFromResolved(
  resolved: ComunicadoDataResolved | undefined,
): number[] {
  const series = resolved?.chart?.series?.[0]?.points ?? resolved?.chart?.points ?? [];
  return series
    .map((point) => parseKpiNumericValue(point?.value))
    .filter((n): n is number => n != null && Number.isFinite(n));
}

/**
 * Resolve flags efetivas sem mutar o bloco persistido.
 * Em `auto`, dados decidem; em `manual`/`off`, respeita flags gravadas.
 */
export function resolveKpiOptionsWithAutoContext(
  options: ComunicadoKpiOptions,
  resolved: ComunicadoDataResolved | undefined,
  metricOverrides?: AutoContextMetricOverrides | null,
): ComunicadoKpiOptions {
  if (effectiveKpiContextMode(options) !== "auto") {
    return options;
  }

  const points = sparklinePointsFromResolved(resolved);
  const hasSeries = points.length >= 2;
  const target = metricOverrides?.target ?? options.target;
  const hasTarget = target != null && Number.isFinite(Number(target));
  const variant: KpiLayoutVariant = options.variant ?? "hero";

  const next: ComunicadoKpiOptions = {
    ...options,
    variant,
    // Gauge genérico off em auto; ícone só se nome INFORMED (≠ default Gauge vazio).
    showIcon: Boolean(options.iconName?.trim()) && options.showIcon !== false,
  };
  if (!next.iconName?.trim()) {
    next.showIcon = false;
    next.iconName = undefined;
  }

  const preferScorecard =
    variant === "scorecard" || (hasTarget && !hasSeries) || (hasTarget && variant === "scorecard");

  if (preferScorecard && hasTarget) {
    next.showProgress = true;
    next.showSparkline = false;
    next.showComparison = true;
    if (next.comparisonMode == null || next.comparisonMode === "none") {
      next.comparisonMode = "target";
    }
    return next;
  }

  if (hasSeries) {
    next.showSparkline = true;
    next.showProgress = false;
    next.showComparison = true;
    if (next.comparisonMode == null || next.comparisonMode === "none") {
      next.comparisonMode = "previous";
    }
    return next;
  }

  if (hasTarget) {
    next.showProgress = true;
    next.showSparkline = false;
    next.showComparison = true;
    if (next.comparisonMode == null || next.comparisonMode === "none") {
      next.comparisonMode = "target";
    }
    return next;
  }

  // Snapshot: só valor — sem inventar sparkline/progress.
  next.showSparkline = false;
  next.showProgress = false;
  next.showComparison = false;
  next.comparisonMode = "none";
  return next;
}
