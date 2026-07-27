import {
  OFFICE_CHART_SERIES_COLOR,
  SERIES_CHART_CATEGORY_PALETTE,
  seriesChartUsesCategoryLegend,
  type SeriesChartKind,
} from "@delpi/plugin-ui/index";
import {
  serializeChartPartRef,
  upsertChartPartState,
  type ComunicadoChartPartsMap,
  type ComunicadoChartViewBlock,
  type ChartViewProjection,
} from "@delpi/tv-dashboard-presentation";

/**
 * Resolve cor efetiva da série N: projection → chartParts → categoryColors → palette / legado.
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
  const fromCat = block.chartOptions?.categoryColors?.[seriesIndex]?.trim();
  if (fromCat) return fromCat;
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

/**
 * Índice de cor ao editar a partir da parte selecionada.
 * Legenda (host) → série 0; item de legenda / série → seriesIndex; fatia (marker) → pointIndex.
 */
export function resolveChartSeriesColorIndex(part: {
  kind: string;
  seriesIndex?: number;
  pointIndex?: number;
} | null | undefined): number {
  if (!part) return 0;
  if (part.kind === "series" && part.seriesIndex != null) return Math.max(0, part.seriesIndex);
  if (part.kind === "marker" && part.pointIndex != null) return Math.max(0, part.pointIndex);
  return 0;
}

function chartUsesCategoryIndexedColors(
  block: Pick<ComunicadoChartViewBlock, "chartType" | "chartProjection">,
): boolean {
  const seriesCount = block.chartProjection?.series?.length ?? 1;
  return seriesChartUsesCategoryLegend(block.chartType as SeriesChartKind, seriesCount);
}

/** Grava cor (e opcionalmente strokeWidth) na série/categoria N — projection + parts + options. */
export function patchChartSeriesAppearance(
  block: Pick<
    ComunicadoChartViewBlock,
    "chartProjection" | "chartParts" | "chartOptions" | "chartType"
  >,
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

  let nextParts = upsertChartPartState(
    block.chartParts,
    { kind: "series", seriesIndex },
    {
      style: {
        ...(color ? { stroke: color, fill: color } : {}),
        ...(patch.strokeWidth != null ? { strokeWidth: patch.strokeWidth } : {}),
      },
    },
  );

  const categoryMode = chartUsesCategoryIndexedColors(block);
  if (color && categoryMode) {
    /* Pizza/funil/empilhado (série única): legenda lista categorias — sync fatia. */
    nextParts = upsertChartPartState(
      nextParts,
      { kind: "marker", seriesIndex: 0, pointIndex: seriesIndex },
      { style: { fill: color } },
    );
  }

  const out: ChartSeriesAppearancePatch = { chartParts: nextParts };
  if (block.chartProjection || seriesList.length > 0) {
    out.chartProjection = {
      ...block.chartProjection,
      categoryField: block.chartProjection?.categoryField,
      series: seriesList.length > 0 ? seriesList : block.chartProjection?.series,
    };
  }

  if (color) {
    const nextOptions: NonNullable<ComunicadoChartViewBlock["chartOptions"]> = {
      ...block.chartOptions,
    };
    if (seriesIndex === 0) {
      nextOptions.seriesColor = color;
    }
    if (categoryMode || (block.chartOptions?.categoryColors?.length ?? 0) > 0) {
      const cats = [...(block.chartOptions?.categoryColors ?? [])];
      while (cats.length <= seriesIndex) {
        cats.push(
          SERIES_CHART_CATEGORY_PALETTE[cats.length % SERIES_CHART_CATEGORY_PALETTE.length] || color,
        );
      }
      cats[seriesIndex] = color;
      nextOptions.categoryColors = cats;
    }
    out.chartOptions = nextOptions;
  }

  return out;
}
