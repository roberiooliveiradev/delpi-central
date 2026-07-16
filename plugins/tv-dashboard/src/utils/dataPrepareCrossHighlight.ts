import type {
  ComunicadoBlock,
  ComunicadoChartViewBlock,
  ChartViewProjection,
} from "@delpi/tv-dashboard-presentation";

export type LinkedChartSeries = {
  chartId: string;
  seriesIndex: number;
  field: string;
  label: string;
  color?: string;
};

/** Séries de chart_view ligadas à fonte — highlight cruzado grid↔série. */
export function linkedChartSeriesForSource(
  blocks: ComunicadoBlock[],
  sourceId: string | null | undefined,
): LinkedChartSeries[] {
  const sid = String(sourceId || "").trim();
  if (!sid) return [];
  const out: LinkedChartSeries[] = [];
  for (const block of blocks) {
    if (block.type !== "chart_view") continue;
    const chart = block as ComunicadoChartViewBlock;
    if (String(chart.dataSourceId || "").trim() !== sid) continue;
    const projection = chart.chartProjection as ChartViewProjection | undefined;
    const series = projection?.series ?? [];
    series.forEach((item, seriesIndex) => {
      const field = String(item.field || "").trim();
      if (!field) return;
      out.push({
        chartId: chart.id,
        seriesIndex,
        field,
        label: String(item.label || field).trim() || field,
        color: item.color,
      });
    });
  }
  return out;
}

export function seriesForColumn(
  linked: LinkedChartSeries[],
  column: string,
): LinkedChartSeries | undefined {
  const col = column.trim();
  return linked.find((item) => item.field === col);
}

export function columnForSelectedSeries(
  linked: LinkedChartSeries[],
  chartId: string | null | undefined,
  seriesIndex: number | null | undefined,
): string | null {
  if (!chartId || seriesIndex == null || seriesIndex < 0) return null;
  const match = linked.find(
    (item) => item.chartId === chartId && item.seriesIndex === seriesIndex,
  );
  return match?.field ?? null;
}
