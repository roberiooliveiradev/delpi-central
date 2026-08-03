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
  | "percent"
  | "compact";

/** Rotação dos rótulos de categoria (eixo X vertical / Y horizontal). */
export type SeriesChartCategoryLabelRotation = "auto" | 0 | -45 | -90;

/** Densidade dos rótulos de categoria quando há colisão. */
export type SeriesChartCategoryLabelOverflow = "skip" | "wrap" | "truncate";

/** Formatação de rótulos de categoria (datas ISO / YYYY-MM). */
export type SeriesChartCategoryLabelFormat =
  | "raw"
  | "autoDate"
  | "day"
  | "month"
  | "year";

export type SeriesChartLegendPosition = "top" | "bottom" | "left" | "right" | "hidden";

/**
 * Orientação dos itens da legenda.
 * - `auto`: coluna em left/right; em top/bottom, coluna se ≥4 categorias (pizza/funil), senão linha.
 * - `row` / `column`: força o layout.
 */
export type SeriesChartLegendLayout = "auto" | "row" | "column";

/**
 * Ordenação das entradas (e das fatias/categorias alinhadas).
 * - `auto`: valor ↓ em pizza/funil (categoria); ordem dos dados nos demais.
 */
export type SeriesChartLegendSort =
  | "auto"
  | "data"
  | "valueDesc"
  | "valueAsc"
  | "nameAsc"
  | "nameDesc";

export type SeriesChartTheme = "light" | "dark";

/**
 * Escala semântica por valor (Excel/Power BI color scales).
 * `off` = cor por índice de categoria/série (padrão).
 */
export type SeriesChartColorScale = {
  mode: "off" | "by_value";
  /** high = pior (refugo, NC) | high = melhor (eficiência, OEE). */
  polarity: "high_is_bad" | "high_is_good";
  /** Id da paleta semântica cujos `colors` definem a rampa. */
  paletteId?: string;
};

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
  /** Linha, coluna ou ajuste automático (padrão). */
  legendLayout?: SeriesChartLegendLayout;
  /** Ordenação das entradas da legenda (e categorias alinhadas no plot). */
  legendSort?: SeriesChartLegendSort;
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
  /**
   * Linha/área com curva suave (Catmull-Rom). Default false = segmentos retos.
   * Só aplica a `line`, `area` e traço de `combo`.
   */
  smoothLines?: boolean;
  valueFormat?: SeriesChartValueFormat;
  /**
   * Casas decimais fixas; `null`/ausente = comportamento do format (auto).
   * Aplica a ticks, data labels e tabela.
   */
  decimalPlaces?: number | null;
  /** Rotação dos rótulos de categoria. Default `auto` (−38° quando necessário). */
  categoryLabelRotation?: SeriesChartCategoryLabelRotation;
  /** Como lidar com rótulos de categoria densos. Default `skip`. */
  categoryLabelOverflow?: SeriesChartCategoryLabelOverflow;
  /** Formato de rótulo de categoria (datas). Default `raw`. */
  categoryLabelFormat?: SeriesChartCategoryLabelFormat;
  seriesColor?: string;
  /**
   * Paleta cíclica (pie/fatias/categorias). Índice 0 ≈ série; índice 1 ≈ fill de área.
   * Vinda de «Alterar cores»; ausente = catálogo Delpi padrão.
   */
  categoryColors?: string[];
  /**
   * Colorir marcas (barra/fatia) pelo valor da medida.
   * Ausente ou `mode: "off"` = comportamento por índice.
   */
  colorScale?: SeriesChartColorScale;
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
export const SERIES_CHART_CHROME_VERSION = 2;

export type SeriesChartPoint = {
  label?: string;
  value?: number | null;
  /** Canal tamanho (bubble); ausente → paint usa |value|. */
  size?: number | null;
  /** Índice estável na série de origem (legenda/cores por categoria). */
  sourceIndex?: number;
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
  | "horizontal_bar"
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
export const DEFAULT_CATEGORY_PADDING_PERCENT = 0;

export const DEFAULT_SERIES_CHART_OPTIONS: SeriesChartOptions = {
  showTitle: true,
  showLegend: true,
  legendPosition: "bottom",
  legendLayout: "auto",
  legendSort: "auto",
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
  smoothLines: false,
  valueFormat: "auto",
  decimalPlaces: null,
  categoryLabelRotation: "auto",
  categoryLabelOverflow: "skip",
  categoryLabelFormat: "raw",
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
  const rawVersion = raw?.chromeVersion ?? 0;
  if (rawVersion >= SERIES_CHART_CHROME_VERSION) {
    return merged;
  }
  const legacyAxisTitlesOff =
    raw?.showXAxisTitle !== true &&
    raw?.showYAxisTitle !== true &&
    !trimChartText(raw?.xAxisTitle) &&
    !trimChartText(raw?.yAxisTitle);
  return {
    ...merged,
    ...(legacyAxisTitlesOff && rawVersion < 1
      ? { showXAxisTitle: true, showYAxisTitle: true }
      : {}),
    // v2: extremos do eixo X no plot (remove padding padrão legado de 6%).
    ...(rawVersion < 2 ? { categoryPaddingPercent: 0 } : {}),
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
    /* Formato: só o que o usuário escolheu (Excel/Power BI). Sem inferência por campo. */
    valueFormat: merged.valueFormat ?? "auto",
  };
}

export const SERIES_CHART_VALUE_FORMAT_OPTIONS = [
  { value: "auto", label: "Geral" },
  { value: "number", label: "Número" },
  { value: "compact", label: "Compacto" },
  { value: "currency", label: "Moeda (R$)" },
  { value: "currency4", label: "Moeda (R$ · 4 casas)" },
  { value: "percent", label: "Percentual" },
] as const;

export const SERIES_CHART_CATEGORY_LABEL_ROTATION_OPTIONS = [
  { value: "auto", label: "Automático" },
  { value: "0", label: "Horizontal (0°)" },
  { value: "-45", label: "−45°" },
  { value: "-90", label: "−90°" },
] as const;

export const SERIES_CHART_CATEGORY_LABEL_OVERFLOW_OPTIONS = [
  { value: "skip", label: "Omitir (pular)" },
  { value: "truncate", label: "Truncar" },
  { value: "wrap", label: "Quebrar linha" },
] as const;

export const SERIES_CHART_CATEGORY_LABEL_FORMAT_OPTIONS = [
  { value: "raw", label: "Como está" },
  { value: "autoDate", label: "Data (auto)" },
  { value: "day", label: "Dia" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
] as const;

export const SERIES_CHART_LEGEND_POSITION_OPTIONS = [
  { value: "top", label: "Acima" },
  { value: "bottom", label: "Abaixo" },
  { value: "right", label: "À direita" },
  { value: "hidden", label: "Oculta" },
] as const;

export const SERIES_CHART_LEGEND_LAYOUT_OPTIONS = [
  { value: "auto", label: "Automático" },
  { value: "row", label: "Linha" },
  { value: "column", label: "Coluna" },
] as const;

export const SERIES_CHART_LEGEND_SORT_OPTIONS = [
  { value: "auto", label: "Automático" },
  { value: "data", label: "Ordem dos dados" },
  { value: "valueDesc", label: "Valor (maior → menor)" },
  { value: "valueAsc", label: "Valor (menor → maior)" },
  { value: "nameAsc", label: "Nome (A → Z)" },
  { value: "nameDesc", label: "Nome (Z → A)" },
] as const;

/** Limiar do padrão automático: legenda em coluna em top/bottom com muitas categorias. */
export const SERIES_CHART_LEGEND_AUTO_COLUMN_MIN_ITEMS = 4;

export type SeriesChartLegendLayoutResolved = "row" | "column";
export type SeriesChartLegendSortResolved = Exclude<SeriesChartLegendSort, "auto">;

/**
 * Resolve layout da legenda. `auto` = coluna nas laterais; em cima/baixo,
 * coluna quando há várias categorias (evita fila horizontal apinhada).
 */
export function resolveSeriesChartLegendLayout(args: {
  position: SeriesChartLegendPosition;
  layout?: SeriesChartLegendLayout | null;
  itemCount?: number;
  usesCategoryLegend?: boolean;
}): SeriesChartLegendLayoutResolved {
  const { position, layout, itemCount = 0, usesCategoryLegend = false } = args;
  if (layout === "row" || layout === "column") return layout;
  if (position === "left" || position === "right") return "column";
  if (usesCategoryLegend && itemCount >= SERIES_CHART_LEGEND_AUTO_COLUMN_MIN_ITEMS) {
    return "column";
  }
  return "row";
}

/**
 * Resolve ordenação. `auto` = valor ↓ em pizza/funil por categoria; senão ordem dos dados.
 */
export function resolveSeriesChartLegendSort(args: {
  chartType: SeriesChartKind;
  sort?: SeriesChartLegendSort | null;
  usesCategoryLegend?: boolean;
}): SeriesChartLegendSortResolved {
  const { chartType, sort, usesCategoryLegend = false } = args;
  if (sort && sort !== "auto") return sort;
  if (usesCategoryLegend && (chartType === "pie" || chartType === "funnel")) {
    return "valueDesc";
  }
  return "data";
}

export function usableSeriesChartPoints(points: SeriesChartPoint[]): SeriesChartPoint[] {
  return points.filter((point) => {
    const raw = point.value;
    if (raw === null || raw === undefined) return false;
    return Number.isFinite(Number(raw));
  });
}

function resolveFractionDigits(
  decimalPlaces: number | null | undefined,
  fallbackMax: number,
  fallbackMin = 0,
): { minimumFractionDigits: number; maximumFractionDigits: number } {
  if (typeof decimalPlaces === "number" && Number.isFinite(decimalPlaces) && decimalPlaces >= 0) {
    const places = Math.min(8, Math.floor(decimalPlaces));
    return { minimumFractionDigits: places, maximumFractionDigits: places };
  }
  return { minimumFractionDigits: fallbackMin, maximumFractionDigits: fallbackMax };
}

export function formatSeriesChartValue(
  value: number,
  format: SeriesChartValueFormat,
  decimalPlaces?: number | null,
): string {
  if (format === "compact") {
    const digits = resolveFractionDigits(decimalPlaces, 1);
    return value.toLocaleString("pt-BR", {
      notation: "compact",
      compactDisplay: "short",
      ...digits,
    });
  }
  if (format === "currency") {
    const hasCents = Math.abs(value % 1) > 1e-9;
    const digits = resolveFractionDigits(decimalPlaces, hasCents ? 2 : 0, hasCents ? 2 : 0);
    return value.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      ...digits,
    });
  }
  if (format === "currency4") {
    const digits = resolveFractionDigits(decimalPlaces, 4, 2);
    return value.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      ...digits,
    });
  }
  if (format === "percent") {
    const digits = resolveFractionDigits(decimalPlaces, 1);
    return `${value.toLocaleString("pt-BR", digits)}%`;
  }
  if (format === "number") {
    const digits = resolveFractionDigits(decimalPlaces, 2);
    return value.toLocaleString("pt-BR", digits);
  }
  /* Geral (auto): número localizado — sem inferir % ou R$ (escolha do usuário). */
  const digits = resolveFractionDigits(decimalPlaces, 2);
  return value.toLocaleString("pt-BR", digits);
}

/** Parse ISO / YYYY-MM / YYYY-MM-DD (e variantes com hora). */
export function parseSeriesChartCategoryDate(raw: string): Date | null {
  const text = raw.trim();
  if (!text) return null;
  const ym = /^(\d{4})-(\d{2})$/.exec(text);
  if (ym) {
    const year = Number(ym[1]);
    const month = Number(ym[2]);
    if (month < 1 || month > 12) return null;
    return new Date(Date.UTC(year, month - 1, 1));
  }
  const ymd = /^(\d{4})-(\d{2})-(\d{2})(?:[T\s].*)?$/.exec(text);
  if (ymd) {
    const year = Number(ymd[1]);
    const month = Number(ymd[2]);
    const day = Number(ymd[3]);
    if (month < 1 || month > 12 || day < 1 || day > 31) return null;
    return new Date(Date.UTC(year, month - 1, day));
  }
  const parsed = Date.parse(text);
  if (!Number.isFinite(parsed)) return null;
  return new Date(parsed);
}

export function formatSeriesChartCategoryLabel(
  raw: string,
  format: SeriesChartCategoryLabelFormat = "raw",
): string {
  if (format === "raw") return raw;
  const date = parseSeriesChartCategoryDate(raw);
  if (!date) return raw;
  if (format === "year") {
    return String(date.getUTCFullYear());
  }
  if (format === "month") {
    return date.toLocaleDateString("pt-BR", { month: "short", year: "numeric", timeZone: "UTC" });
  }
  if (format === "day") {
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      timeZone: "UTC",
    });
  }
  /* autoDate: curto e legível */
  const hasDay = /^\d{4}-\d{2}-\d{2}/.test(raw.trim());
  if (hasDay) {
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      timeZone: "UTC",
    });
  }
  return date.toLocaleDateString("pt-BR", { month: "short", year: "2-digit", timeZone: "UTC" });
}

/** Trunca rótulo de categoria com reticências (overflow=truncate). */
export function truncateSeriesChartCategoryLabel(label: string, maxChars = 12): string {
  const text = label.trim();
  if (text.length <= maxChars) return text;
  return `${text.slice(0, Math.max(1, maxChars - 1))}…`;
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
  // Domínio "nice" que sempre cobre [min, max] — evita clipar série no teto do plot
  // (ex.: economia ~875 com ticks até 800 → área plana no topo).
  const niceMin = Math.floor(min / step) * step;
  let niceMax = Math.ceil(max / step) * step;
  // Pico exatamente no tick nice (ex.: 28 000) colava no clipPath → área «vazando»
  // / achatada no topo. Reserva sempre um degrau acima do dataMax.
  if (niceMax <= max) {
    niceMax = Number((niceMax + step).toFixed(6));
  }
  const ticks: number[] = [];
  for (let value = niceMin; value <= niceMax + step * 0.001; value += step) {
    ticks.push(Number(value.toFixed(6)));
    if (ticks.length >= count + 4) break;
  }
  if (ticks.length < 2) return [min, max];
  const first = ticks[0]!;
  const last = ticks[ticks.length - 1]!;
  if (first > min) ticks.unshift(Number((first - step).toFixed(6)));
  if (last < max) ticks.push(Number(niceMax.toFixed(6)));
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

/**
 * Mapeia um valor na rampa semântica (stops discretos).
 * `high_is_bad`: valor alto → fim da rampa (ex. vermelho em Melhor→pior).
 * `high_is_good`: valor alto → início da rampa.
 */
export function resolveValueScaleColor(args: {
  value: number;
  min: number;
  max: number;
  colors: readonly string[];
  polarity: "high_is_bad" | "high_is_good";
}): string {
  const colors = args.colors.filter((c) => typeof c === "string" && c.trim());
  if (colors.length === 0) return SERIES_CHART_CATEGORY_PALETTE[0]!;
  if (colors.length === 1) return colors[0]!;

  const raw = Number(args.value);
  const min = Number(args.min);
  const max = Number(args.max);
  let t = 0.5;
  if (Number.isFinite(raw) && Number.isFinite(min) && Number.isFinite(max) && max !== min) {
    t = (raw - min) / (max - min);
  }
  t = Math.min(1, Math.max(0, t));
  if (args.polarity === "high_is_good") {
    t = 1 - t;
  }
  const bucket = Math.min(colors.length - 1, Math.floor(t * colors.length));
  /* Valor no máximo cai no último stop (não no penúltimo por floor). */
  const index = t >= 1 ? colors.length - 1 : bucket;
  return colors[index]!;
}

/** Min/max finitos de uma lista de valores (ignora null/NaN). */
export function seriesValueExtent(
  values: readonly (number | null | undefined)[],
): { min: number; max: number } {
  let min = Number.POSITIVE_INFINITY;
  let max = Number.NEGATIVE_INFINITY;
  for (const raw of values) {
    if (raw == null) continue;
    const n = Number(raw);
    if (!Number.isFinite(n)) continue;
    if (n < min) min = n;
    if (n > max) max = n;
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return { min: 0, max: 0 };
  }
  return { min, max };
}
