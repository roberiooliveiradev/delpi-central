/**
 * Modelo escalar do gráfico velocímetro (`chartType: gauge`).
 * Único ponto lido pelo paint — value/goal/accent a partir de projection + options + resolved.
 */

import type { ComunicadoChartOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartViewBlock, ComunicadoDataResolved } from "./comunicadoTypes";
import { resolveEffectiveChartGoal } from "./resolveEffectiveChartGoal";

export type GaugeChartModel = {
  value: number | null;
  goal: number | null;
  min: number;
  max: number;
  label: string;
  unit: string;
  accentColor?: string;
  showTitle: boolean;
  title: string;
};

function asFinite(value: unknown): number | null {
  if (value == null || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function resolveGaugeValue(resolved: ComunicadoDataResolved | undefined): number | null {
  const fromKpi = asFinite(resolved?.kpi?.value);
  if (fromKpi != null) return fromKpi;
  const points = resolved?.chart?.points ?? [];
  for (let i = points.length - 1; i >= 0; i -= 1) {
    const v = asFinite(points[i]?.value);
    if (v != null) return v;
  }
  const series = resolved?.chart?.series ?? [];
  for (const entry of series) {
    const pts = entry.points ?? [];
    for (let i = pts.length - 1; i >= 0; i -= 1) {
      const v = asFinite(pts[i]?.value);
      if (v != null) return v;
    }
  }
  return null;
}

export function resolveGaugeChartModel(args: {
  block: Pick<ComunicadoChartViewBlock, "chartOptions" | "chartProjection">;
  resolved?: ComunicadoDataResolved | null;
  options?: ComunicadoChartOptions | null;
}): GaugeChartModel {
  const options = args.options ?? args.block.chartOptions ?? {};
  const resolved = args.resolved ?? undefined;
  const value = resolveGaugeValue(resolved);
  const goal = resolveEffectiveChartGoal({
    goalLineValue: options.goalLineValue,
    projectedGoal: resolved?.chart?.projectedGoal,
  });
  const label =
    String(resolved?.kpi?.label ?? resolved?.label ?? options.seriesName ?? options.title ?? "").trim() ||
    "Valor";
  const title =
    String(options.title ?? resolved?.label ?? resolved?.kpi?.label ?? label).trim() || label;
  const accent = String(options.seriesColor ?? "").trim() || undefined;
  const maxFromGoal = goal != null && goal > 0 ? Math.max(100, Math.ceil(goal)) : 100;
  const maxFromValue = value != null && value > maxFromGoal ? Math.ceil(value) : maxFromGoal;
  return {
    value,
    goal,
    min: 0,
    max: maxFromValue > 0 ? maxFromValue : 100,
    label,
    unit: "%",
    accentColor: accent,
    showTitle: options.showTitle !== false,
    title,
  };
}
