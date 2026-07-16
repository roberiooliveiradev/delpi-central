import {
  OFFICE_CHART_SERIES_COLOR,
  SERIES_CHART_CATEGORY_PALETTE,
} from "@delpi/plugin-ui/index";
import {
  serializeChartPartRef,
  upsertChartPartState,
  type ComunicadoChartPartsMap,
  type ComunicadoChartViewBlock,
  type ChartViewProjection,
} from "@delpi/tv-dashboard-presentation";

/**
 * Resolve cor efetiva da série N: projection → chartParts → palette / legado.
 */
export function resolveChartSeriesAppearanceColor(
  block: Pick<ComunicadoChartViewBlock, "chartProjection" | "chartParts" | "chartOptions">,
  seriesIndex: number,
): string {
  const fromProj = block.chartProjection?.series?.[seriesIndex]?.color?.trim();
  if (fromProj) return fromProj;
  const partKey = serializeChartPartRef({ kind: "series", seriesIndex });
  const fromPart =
    block.chartParts?.[partKey]?.style?.stroke?.trim() ||
    block.chartParts?.[partKey]?.style?.fill?.trim();
  if (fromPart) return fromPart;
  if (seriesIndex === 0 && block.chartOptions?.seriesColor?.trim()) {
    return block.chartOptions.seriesColor.trim();
  }
  return (
    SERIES_CHART_CATEGORY_PALETTE[seriesIndex % SERIES_CHART_CATEGORY_PALETTE.length] ||
    OFFICE_CHART_SERIES_COLOR
  );
}

export type ChartSeriesAppearancePatch = {
  chartProjection?: ChartViewProjection;
  chartParts?: ComunicadoChartPartsMap;
  chartOptions?: ComunicadoChartViewBlock["chartOptions"];
};

/** Grava cor (e opcionalmente strokeWidth) na série N — projection + parts. */
export function patchChartSeriesAppearance(
  block: Pick<ComunicadoChartViewBlock, "chartProjection" | "chartParts" | "chartOptions">,
  seriesIndex: number,
  patch: { color?: string; strokeWidth?: number },
): ChartSeriesAppearancePatch {
  const seriesList = [...(block.chartProjection?.series ?? [])];
  const color = patch.color?.trim();
  if (color && seriesList[seriesIndex]) {
    seriesList[seriesIndex] = { ...seriesList[seriesIndex]!, color };
  } else if (color && seriesIndex === 0 && seriesList.length === 0) {
    // Sem projection: só options legado.
  }

  const nextParts = upsertChartPartState(
    block.chartParts,
    { kind: "series", seriesIndex },
    {
      style: {
        ...(color ? { stroke: color, fill: color } : {}),
        ...(patch.strokeWidth != null ? { strokeWidth: patch.strokeWidth } : {}),
      },
    },
  );

  const out: ChartSeriesAppearancePatch = { chartParts: nextParts };
  if (block.chartProjection || seriesList.length > 0) {
    out.chartProjection = {
      ...block.chartProjection,
      categoryField: block.chartProjection?.categoryField,
      series: seriesList.length > 0 ? seriesList : block.chartProjection?.series,
    };
  }
  if (seriesIndex === 0 && color) {
    out.chartOptions = { ...block.chartOptions, seriesColor: color };
  }
  return out;
}
