export type ComunicadoChartValueFormat = "auto" | "number" | "currency" | "percent";

export type ComunicadoChartLegendPosition = "top" | "bottom" | "right" | "hidden";

/** Opções de apresentação do bloco `chart_view` (persistidas no native_config). */
export type ComunicadoChartOptions = {
  title?: string;
  showTitle?: boolean;
  seriesName?: string;
  showLegend?: boolean;
  legendPosition?: ComunicadoChartLegendPosition;
  showAxes?: boolean;
  showXAxisLabels?: boolean;
  showYAxisLabels?: boolean;
  showXAxisTitle?: boolean;
  showYAxisTitle?: boolean;
  xAxisTitle?: string;
  yAxisTitle?: string;
  showDataLabels?: boolean;
  showDataTable?: boolean;
  showGrid?: boolean;
  showVerticalGrid?: boolean;
  showMarkers?: boolean;
  valueFormat?: ComunicadoChartValueFormat;
  seriesColor?: string;
};

export type SeriesChartPoint = {
  label?: string;
  value?: number | null;
};

export type SeriesChartKind = "line" | "bar";

export const DEFAULT_COMUNICADO_CHART_OPTIONS: ComunicadoChartOptions = {
  showTitle: true,
  showLegend: true,
  legendPosition: "bottom",
  showAxes: true,
  showXAxisLabels: true,
  showYAxisLabels: true,
  showXAxisTitle: false,
  showYAxisTitle: false,
  showDataLabels: false,
  showDataTable: false,
  showGrid: true,
  showVerticalGrid: false,
  showMarkers: true,
  valueFormat: "auto",
  seriesColor: "#0d7a8c",
};

export function mergeComunicadoChartOptions(
  partial?: ComunicadoChartOptions | null,
): ComunicadoChartOptions {
  return { ...DEFAULT_COMUNICADO_CHART_OPTIONS, ...(partial ?? {}) };
}

export function resolveChartDisplayOptions(
  blockOptions: ComunicadoChartOptions | undefined,
  resolved?: { label?: string; kpi?: { label?: string } },
): ComunicadoChartOptions {
  const merged = mergeComunicadoChartOptions(blockOptions);
  const fallbackTitle = resolved?.label ?? resolved?.kpi?.label ?? "";
  return {
    ...merged,
    title: merged.title?.trim() || fallbackTitle,
    seriesName: merged.seriesName?.trim() || merged.title?.trim() || fallbackTitle || "Série",
  };
}

export const CHART_VALUE_FORMAT_OPTIONS = [
  { value: "auto", label: "Automático" },
  { value: "number", label: "Número" },
  { value: "currency", label: "Moeda (R$)" },
  { value: "percent", label: "Percentual" },
] as const;

export const CHART_LEGEND_POSITION_OPTIONS = [
  { value: "top", label: "Acima" },
  { value: "bottom", label: "Abaixo" },
  { value: "right", label: "À direita" },
  { value: "hidden", label: "Oculta" },
] as const;

export function usableSeriesChartPoints(points: SeriesChartPoint[]): SeriesChartPoint[] {
  return points.filter((point) => {
    const raw = point.value;
    if (raw === null || raw === undefined) return false;
    return Number.isFinite(Number(raw));
  });
}

export function formatSeriesChartValue(
  value: number,
  format: ComunicadoChartValueFormat,
): string {
  if (format === "currency") {
    return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
  }
  if (format === "percent") {
    return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
  }
  if (format === "number") {
    return value.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  }
  if (Math.abs(value) <= 100 && !Number.isInteger(value)) {
    return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
  }
  if (Math.abs(value) >= 1000) {
    return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
  }
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

export function resolveSeriesChartTicks(min: number, max: number, count = 5): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [0, 1];
  if (min === max) {
    const pad = Math.max(Math.abs(min) * 0.1, 1);
    min -= pad;
    max += pad;
  }
  const range = max - min;
  const rawStep = range / Math.max(count - 1, 1);
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep || 1)));
  const step = Math.ceil(rawStep / magnitude) * magnitude || 1;
  const niceMin = Math.floor(min / step) * step;
  const ticks: number[] = [];
  for (let value = niceMin; value <= max + step * 0.001; value += step) {
    ticks.push(Number(value.toFixed(6)));
    if (ticks.length >= count + 2) break;
  }
  if (ticks.length < 2) return [min, max];
  return ticks;
}
