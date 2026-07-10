export type SeriesChartValueFormat = "auto" | "number" | "currency" | "percent";

export type SeriesChartLegendPosition = "top" | "bottom" | "right" | "hidden";

export type SeriesChartTheme = "light" | "dark";

export type SeriesChartOptions = {
  title?: string;
  showTitle?: boolean;
  seriesName?: string;
  showLegend?: boolean;
  legendPosition?: SeriesChartLegendPosition;
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
  valueFormat?: SeriesChartValueFormat;
  seriesColor?: string;
  /** Padrão: fundo claro. */
  theme?: SeriesChartTheme;
  backgroundColor?: string;
};

export type SeriesChartPoint = {
  label?: string;
  value?: number | null;
};

export type SeriesChartKind = "line" | "bar";

export const DEFAULT_SERIES_CHART_OPTIONS: SeriesChartOptions = {
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
  theme: "light",
};

export function mergeSeriesChartOptions(partial?: SeriesChartOptions | null): SeriesChartOptions {
  return { ...DEFAULT_SERIES_CHART_OPTIONS, ...(partial ?? {}) };
}

export function resolveSeriesChartDisplayOptions(
  blockOptions: SeriesChartOptions | undefined,
  resolved?: { label?: string; kpi?: { label?: string } },
): SeriesChartOptions {
  const merged = mergeSeriesChartOptions(blockOptions);
  const fallbackTitle = resolved?.label ?? resolved?.kpi?.label ?? "";
  return {
    ...merged,
    title: merged.title?.trim() || fallbackTitle,
    seriesName: merged.seriesName?.trim() || merged.title?.trim() || fallbackTitle || "Série",
  };
}

export const SERIES_CHART_VALUE_FORMAT_OPTIONS = [
  { value: "auto", label: "Automático" },
  { value: "number", label: "Número" },
  { value: "currency", label: "Moeda (R$)" },
  { value: "percent", label: "Percentual" },
] as const;

export const SERIES_CHART_LEGEND_POSITION_OPTIONS = [
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

export function formatSeriesChartValue(value: number, format: SeriesChartValueFormat): string {
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

const LIGHT_CHART_THEME = {
  bg: "#ffffff",
  text: "#1e293b",
  textStrong: "#0f172a",
  muted: "#64748b",
  grid: "color-mix(in srgb, #94a3b8 35%, transparent)",
} as const;

const DARK_CHART_THEME = {
  bg: "#0b1520",
  text: "#e2e8f0",
  textStrong: "#f8fafc",
  muted: "#94a3b8",
  grid: "color-mix(in srgb, #94a3b8 25%, transparent)",
} as const;

export function seriesChartThemeStyle(options: SeriesChartOptions): Record<string, string> {
  const theme = options.theme ?? "light";
  const palette = theme === "dark" ? DARK_CHART_THEME : LIGHT_CHART_THEME;
  const style: Record<string, string> = {
    "--delpi-ui-series-chart-bg": options.backgroundColor ?? palette.bg,
    "--delpi-ui-series-chart-text": palette.text,
    "--delpi-ui-series-chart-text-strong": palette.textStrong,
    "--delpi-ui-series-chart-muted": palette.muted,
    "--delpi-ui-series-chart-grid": palette.grid,
  };
  return style;
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
