import type { ChartTopFilter, ChartZoomWindow } from "./chartPresentationUx";

/** Estado da UX do gráfico — preservado ao expandir o modal. */
export type ChartViewState = {
  chartTypeOverride: string | null;
  axisXOverride: string | null;
  axisYOverride: string | null;
  categoryFilterKey: string | null;
  categoryFilterValue: string | null;
  topFilter: ChartTopFilter;
  zoomWindow: ChartZoomWindow;
  periodCompareEnabled: boolean;
};

export function createDefaultChartViewState(): ChartViewState {
  return {
    chartTypeOverride: null,
    axisXOverride: null,
    axisYOverride: null,
    categoryFilterKey: null,
    categoryFilterValue: null,
    topFilter: "all",
    zoomWindow: "all",
    periodCompareEnabled: false,
  };
}
