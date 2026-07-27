import {
  DECK_CATEGORY_PALETTE,
  DECK_THEME_DARK,
  DECK_THEME_LIGHT,
  OFFICE_CHART_AREA_FILL,
  OFFICE_CHART_SERIES_COLOR,
} from "../../theme/deckColorCatalog";
import type { SeriesChartDataLabelsConfig } from "./seriesChartDataLabels";

export type SeriesChartValueFormat =
  | "auto"
  | "number"
  | "currency"
  | "currency4"
  | "percent";

export type SeriesChartLegendPosition = "top" | "bottom" | "left" | "right" | "hidden";

export type SeriesChartTheme = "light" | "dark";

/** @deprecated Preferir import de `@delpi/plugin-ui` theme / DECK_COLOR_*. */
export {
  OFFICE_CHART_AREA_FILL,
  OFFICE_CHART_AREA_STROKE,
  OFFICE_CHART_PLOT_FILL,
  OFFICE_CHART_PLOT_STROKE,
  OFFICE_CHART_SERIES_COLOR,
} from "../../theme/deckColorCatalog";

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
  /**
   * Conteúdo/posição dos rótulos (Excel/PPT Label Options).
   * Só aplica com `showDataLabels: true`.
   */
  dataLabels?: SeriesChartDataLabelsConfig;
  showDataTable?: boolean;
  showGrid?: boolean;
  showVerticalGrid?: boolean;
  showMarkers?: boolean;
  valueFormat?: SeriesChartValueFormat;
  seriesColor?: string;
  /**
   * Paleta cíclica (pie/fatias/categorias). Índice 0 ≈ série; índice 1 ≈ fill de área.
   * Vinda de «Alterar cores»; ausente = catálogo Delpi padrão.
   */
  categoryColors?: string[];
  /** Padrão Office: fundo claro. `dark` só sob pedido explícito. */
  theme?: SeriesChartTheme;
  backgroundColor?: string;
  /**
   * Padding de categoria no eixo X (% da largura do plot em cada lado).
   * Evita marcadores/rótulos colados na borda (Excel Plot Area padding).
   * Default: `DEFAULT_CATEGORY_PADDING_PERCENT`.
   */
  categoryPaddingPercent?: number;
  /**
   * Versão do chrome do gráfico. Ausente = bloco legado (pré–títulos de eixo ON).
   * Usado só no load para migrar defaults sem reabrir o que o usuário desligou depois.
   */
  chromeVersion?: number;
};

/** Chrome atual: títulos de eixo ligados por padrão + fallback da rota. */
export const SERIES_CHART_CHROME_VERSION = 1;

export type SeriesChartPoint = {
  label?: string;
  value?: number | null;
};

/** Série nomeada para gráficos multi-série (overlay). */
export type SeriesChartSeriesSpec = {
  name: string;
  points: SeriesChartPoint[];
  color?: string;
  /** Eixo Y secundário (direita). */
  plotOn?: "primary" | "secondary";
};

/** Tipos com paint SVG nativo (4H.7 + avançados). */
export type SeriesChartKind =
  | "line"
  | "bar"
  | "area"
  | "pie"
  | "combo"
  | "stacked_bar"
  | "histogram"
  | "scatter"
  | "bubble"
  | "radar"
  | "waterfall"
  | "funnel";

/** Paleta cíclica para fatias / segmentos / categorias (Office-like). */
export const SERIES_CHART_CATEGORY_PALETTE = DECK_CATEGORY_PALETTE;

/** Padding padrão de categoria (~3% de cada lado do plot). */
export const DEFAULT_CATEGORY_PADDING_PERCENT = 6;

export const DEFAULT_SERIES_CHART_OPTIONS: SeriesChartOptions = {
  showTitle: true,
  showLegend: true,
  legendPosition: "bottom",
  showAxes: true,
  showXAxisLabels: true,
  showYAxisLabels: true,
  showXAxisTitle: true,
  showYAxisTitle: true,
  showDataLabels: false,
  showDataTable: false,
  showGrid: true,
  showVerticalGrid: false,
  showMarkers: true,
  valueFormat: "auto",
  seriesColor: OFFICE_CHART_SERIES_COLOR,
  theme: "light",
  backgroundColor: OFFICE_CHART_AREA_FILL,
  categoryPaddingPercent: DEFAULT_CATEGORY_PADDING_PERCENT,
  chromeVersion: SERIES_CHART_CHROME_VERSION,
};

/**
 * Migra options no load do bloco (JSON antigo).
 * Blocos sem `chromeVersion` e com eixos off sem texto → liga títulos (novo padrão).
 * Blocos já na versão atual preservam escolha do usuário (ex.: eixos desligados).
 */
export function migrateSeriesChartOptionsOnLoad(
  raw?: SeriesChartOptions | null,
): SeriesChartOptions {
  const merged = mergeSeriesChartOptions(raw);
  if ((raw?.chromeVersion ?? 0) >= SERIES_CHART_CHROME_VERSION) {
    return merged;
  }
  const legacyAxisTitlesOff =
    raw?.showXAxisTitle !== true &&
    raw?.showYAxisTitle !== true &&
    !trimChartText(raw?.xAxisTitle) &&
    !trimChartText(raw?.yAxisTitle);
  return {
    ...merged,
    ...(legacyAxisTitlesOff ? { showXAxisTitle: true, showYAxisTitle: true } : {}),
    chromeVersion: SERIES_CHART_CHROME_VERSION,
  };
}

export function mergeSeriesChartOptions(partial?: SeriesChartOptions | null): SeriesChartOptions {
  const merged = { ...DEFAULT_SERIES_CHART_OPTIONS, ...(partial ?? {}) };
  /* Migra default legado (teal) → azul das formas Office. */
  if (merged.seriesColor === "#0d7a8c") {
    merged.seriesColor = OFFICE_CHART_SERIES_COLOR;
  }
  if (!merged.backgroundColor) {
    merged.backgroundColor = OFFICE_CHART_AREA_FILL;
  }
  if (!merged.theme) {
    merged.theme = "light";
  }
  return merged;
}

/** Metadados da rota/enrichment usados como fallback de título e eixos (igual ao título do gráfico). */
export type SeriesChartResolvedMeta = {
  label?: string | null;
  kpi?: { label?: string | null } | null;
  table?: {
    columns?: Array<{ key?: string; label?: string } | null> | null;
  } | null;
};

function trimChartText(value: unknown): string {
  if (typeof value !== "string") return "";
  return value.trim();
}

/** Eixo X: 1ª coluna tabular da rota (ex.: «Período») ou fallback. */
function defaultXAxisTitleFromResolved(resolved?: SeriesChartResolvedMeta | null): string {
  const cols = resolved?.table?.columns;
  if (Array.isArray(cols)) {
    for (const col of cols) {
      const label = trimChartText(col?.label);
      if (label) return label;
    }
  }
  return "Período";
}

/** Eixo Y: 2ª coluna (métrica) ou label/KPI da rota — mesma fonte do título. */
function defaultYAxisTitleFromResolved(resolved?: SeriesChartResolvedMeta | null): string {
  const cols = resolved?.table?.columns;
  if (Array.isArray(cols) && cols.length > 1) {
    const valueLabel = trimChartText(cols[1]?.label);
    if (valueLabel) return valueLabel;
  }
  return trimChartText(resolved?.kpi?.label) || trimChartText(resolved?.label);
}

export function resolveSeriesChartDisplayOptions(
  blockOptions: SeriesChartOptions | undefined,
  resolved?: SeriesChartResolvedMeta | null,
): SeriesChartOptions {
  const merged = mergeSeriesChartOptions(blockOptions);
  const fallbackTitle = trimChartText(resolved?.label) || trimChartText(resolved?.kpi?.label);
  const xAxisTitle = trimChartText(merged.xAxisTitle) || defaultXAxisTitleFromResolved(resolved);
  const yAxisTitle =
    trimChartText(merged.yAxisTitle) || defaultYAxisTitleFromResolved(resolved) || fallbackTitle;
  return {
    ...merged,
    title: trimChartText(merged.title) || fallbackTitle,
    seriesName:
      trimChartText(merged.seriesName) || trimChartText(merged.title) || fallbackTitle || "Série",
    xAxisTitle: xAxisTitle || undefined,
    yAxisTitle: yAxisTitle || undefined,
  };
}

export const SERIES_CHART_VALUE_FORMAT_OPTIONS = [
  { value: "auto", label: "Automático" },
  { value: "number", label: "Número" },
  { value: "currency", label: "Moeda (R$)" },
  { value: "currency4", label: "Moeda (R$ · 4 casas)" },
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
  if (format === "currency4") {
    return value.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    });
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

const LIGHT_CHART_THEME = DECK_THEME_LIGHT;
const DARK_CHART_THEME = DECK_THEME_DARK;

export function seriesChartThemeStyle(options: SeriesChartOptions): Record<string, string> {
  const theme = options.theme ?? "light";
  const palette = theme === "dark" ? DARK_CHART_THEME : LIGHT_CHART_THEME;
  const bg = options.backgroundColor ?? palette.bg;
  const style: Record<string, string> = {
    "--delpi-ui-series-chart-bg": bg,
    "--delpi-ui-series-chart-text": palette.text,
    "--delpi-ui-series-chart-text-strong": palette.textStrong,
    "--delpi-ui-series-chart-muted": palette.muted,
    "--delpi-ui-series-chart-grid": palette.grid,
    /* Aliases para o prefixo `tdp-series-chart` (presentation / TV). */
    "--tdp-series-chart-bg": bg,
    "--tdp-series-chart-text": palette.text,
    "--tdp-series-chart-text-strong": palette.textStrong,
    "--tdp-series-chart-muted": palette.muted,
    "--tdp-series-chart-grid": palette.grid,
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

/**
 * Cor por categoria/fatia (pie, empilhado, funil).
 * Com `categoryColors` da paleta Alterar cores; senão série 0 + catálogo Delpi.
 */
export function resolveSeriesCategoryColor(
  index: number,
  seriesColor: string | undefined,
  categoryColors?: string[] | null,
  fallbackPalette: readonly string[] = SERIES_CHART_CATEGORY_PALETTE,
): string {
  if (categoryColors && categoryColors.length > 0) {
    return categoryColors[index % categoryColors.length] ?? seriesColor ?? fallbackPalette[0]!;
  }
  if (index === 0) return seriesColor ?? fallbackPalette[0]!;
  return fallbackPalette[index % fallbackPalette.length]!;
}
