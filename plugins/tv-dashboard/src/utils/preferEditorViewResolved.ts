import type { ComunicadoDataResolved } from "@delpi/tv-dashboard-presentation";

function countFiniteChartPoints(resolved?: ComunicadoDataResolved | null): number {
  if (!resolved?.chart) return 0;
  const points = resolved.chart.points ?? [];
  const fromPoints = points.filter((point) => {
    const n = typeof point.value === "number" ? point.value : Number(point.value);
    return Number.isFinite(n);
  }).length;
  if (fromPoints > 0) return fromPoints;
  return (resolved.chart.series ?? []).reduce((sum, series) => {
    const pts = series.points ?? [];
    return (
      sum +
      pts.filter((point) => {
        const n = typeof point.value === "number" ? point.value : Number(point.value);
        return Number.isFinite(n);
      }).length
    );
  }, 0);
}

function hasTextDisplay(resolved?: ComunicadoDataResolved | null): boolean {
  if (!resolved || resolved.presentationStale === true) return false;
  if (typeof resolved.displayText === "string" && resolved.displayText.length > 0) return true;
  return Array.isArray(resolved.displayRuns) && resolved.displayRuns.length > 0;
}

function hasKpiDisplay(resolved?: ComunicadoDataResolved | null): boolean {
  if (!resolved || resolved.presentationStale === true) return false;
  if (typeof resolved.kpi?.displayValue === "string") return true;
  if (resolved.kpiPresentation && typeof resolved.kpiPresentation.valueDisplay === "string") {
    return true;
  }
  return false;
}

/**
 * Escolhe linked enrich vs resolved da fonte para paint no editor.
 * Preferir displayText/displayRuns/bake quando houver sinal pintavel; se o bake
 * esvaziar o grafico mas a fonte ainda tem serie, cair na fonte (resiliencia).
 */
export function preferEditorViewResolved(args: {
  blockType: string;
  linked?: ComunicadoDataResolved | null;
  source?: ComunicadoDataResolved | null;
}): ComunicadoDataResolved | undefined {
  const linked = args.linked ?? undefined;
  const source = args.source ?? undefined;
  if (!linked && !source) return undefined;
  if (!linked) return source;
  if (!source) return linked;

  if (args.blockType === "chart_view") {
    const linkedPts = countFiniteChartPoints(linked);
    const sourcePts = countFiniteChartPoints(source);
    if (linked.chart?.gaugeModel) return linked;
    if (linkedPts > 0) return linked;
    if (sourcePts > 0) return source;
    return linked;
  }

  if (args.blockType === "kpi_view") {
    if (hasKpiDisplay(linked)) return linked;
    if (hasKpiDisplay(source)) return source;
    // Bake sem display* ainda pode ter value — mas paint exige display; prefer linked.
    return linked;
  }

  if (args.blockType === "table_view") {
    const linkedRows = linked.table?.displayRows?.length ?? linked.table?.rows?.length ?? 0;
    const sourceRows = source.table?.displayRows?.length ?? source.table?.rows?.length ?? 0;
    if (linkedRows > 0) return linked;
    if (sourceRows > 0) return source;
    return linked;
  }

  // text / heading / shape
  if (hasTextDisplay(linked)) return linked;
  if (hasTextDisplay(source)) return source;
  return linked;
}
