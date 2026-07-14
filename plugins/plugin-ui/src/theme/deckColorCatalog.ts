/**
 * Catálogo de cores padrão do deck TV / Office — fonte única.
 * Gráficos, KPIs, tabelas, formas, linhas e pontos herdam estes tokens.
 * Não duplicar hex soltos nos consumidores; importar daqui.
 */

/** Accent / série / preenchimento de forma (azul DELPI). */
export const DECK_COLOR_ACCENT = "#089bdb";

/** Superfície clara (fundo de gráfico, KPI, tabela). */
export const DECK_COLOR_SURFACE = "#ffffff";

/** Borda / contorno de área (Office plot). */
export const DECK_COLOR_BORDER = "#b4b4b4";

/** Texto principal sobre superfície clara. */
export const DECK_COLOR_TEXT = "#1e293b";

/** Texto forte (valores, títulos). */
export const DECK_COLOR_TEXT_STRONG = "#0f172a";

/** Texto secundário / eixos / legendas. */
export const DECK_COLOR_MUTED = "#64748b";

/** Contorno padrão de forma sobre fill accent (Office) — preto. */
export const DECK_COLOR_SHAPE_STROKE = "#000000";

/** Header de tabela (zebra leve). */
export const DECK_COLOR_TABLE_HEADER_BG = "#f1f5f9";

/** Célula de tabela. */
export const DECK_COLOR_TABLE_CELL_BG = "#ffffff";

/** Borda de tabela. */
export const DECK_COLOR_TABLE_BORDER = "#e2e8f0";

/** Texto de célula. */
export const DECK_COLOR_TABLE_CELL_TEXT = "#334155";

/** Paleta cíclica (fatias, categorias, múltiplas séries). */
export const DECK_CATEGORY_PALETTE = [
  DECK_COLOR_ACCENT,
  "#0d9488",
  "#f59e0b",
  "#6366f1",
  "#ef4444",
  "#84cc16",
  "#a855f7",
  "#64748b",
] as const;

/** Tema claro (padrão Office — alinhado ao gráfico). */
export const DECK_THEME_LIGHT = {
  bg: DECK_COLOR_SURFACE,
  text: DECK_COLOR_TEXT,
  textStrong: DECK_COLOR_TEXT_STRONG,
  muted: DECK_COLOR_MUTED,
  accent: DECK_COLOR_ACCENT,
  border: DECK_COLOR_BORDER,
  grid: "color-mix(in srgb, #64748b 55%, transparent)",
} as const;

/** Tema escuro (opt-in — slides/master nativos). */
export const DECK_THEME_DARK = {
  bg: "#0b1520",
  text: "#e2e8f0",
  textStrong: "#f8fafc",
  muted: "#94a3b8",
  accent: DECK_COLOR_ACCENT,
  border: "color-mix(in srgb, #089bdb 28%, transparent)",
  grid: "color-mix(in srgb, #cbd5e1 45%, transparent)",
} as const;

export type DeckColorTheme = typeof DECK_THEME_LIGHT;

/** Defaults de forma / linha / ponto. */
export const DECK_SHAPE_DEFAULTS = {
  fill: DECK_COLOR_ACCENT,
  stroke: DECK_COLOR_SHAPE_STROKE,
  /** Traço de linha/seta — mesmo azul do preenchimento das formas. */
  lineStroke: DECK_COLOR_ACCENT,
} as const;

/** Defaults de gráfico (série + área) — chrome alinhado ao KPI. */
export const DECK_CHART_DEFAULTS = {
  seriesColor: DECK_COLOR_ACCENT,
  areaFill: DECK_COLOR_SURFACE,
  areaStroke: DECK_COLOR_BORDER,
  plotFill: DECK_COLOR_SURFACE,
  plotStroke: DECK_COLOR_BORDER,
  backgroundColor: DECK_COLOR_SURFACE,
  /** Raio padrão da área do gráfico (px) — paridade com KPI. */
  borderRadius: 16,
  borderColor: DECK_COLOR_BORDER,
  borderWidth: 1,
  boxShadow:
    "0 1px 2px rgba(15, 23, 42, 0.06), 0 12px 28px rgba(15, 23, 42, 0.10)",
} as const;

/** Defaults de KPI (mesmo visual claro do gráfico) — chrome + tipografia. */
export const DECK_KPI_DEFAULTS = {
  backgroundColor: DECK_COLOR_SURFACE,
  valueColor: DECK_COLOR_TEXT_STRONG,
  labelColor: DECK_COLOR_MUTED,
  accent: DECK_COLOR_ACCENT,
  /** Ícone Lucide padrão do card. */
  iconName: "Gauge",
  /** Raio padrão do card (px). */
  borderRadius: 16,
  /** Contorno suave alinhado ao catálogo. */
  borderColor: DECK_COLOR_BORDER,
  borderWidth: 1,
  /**
   * Sombra padrão do card (contato + ambiente).
   * Persistida em `kpiParts.card.style.boxShadow`.
   */
  boxShadow:
    "0 1px 2px rgba(15, 23, 42, 0.06), 0 12px 28px rgba(15, 23, 42, 0.10)",
  /**
   * Frame inicial do bloco no palco (% do slide).
   * Compacto o suficiente para título + valor + ícone sem área morta.
   */
  frame: { x: 8, y: 32, w: 20, h: 15 },
} as const;

/**
 * Defaults do bloco filtro (input) — superfície Office + sombra na moldura;
 * campo de edição com contorno preto (forma).
 */
export const DECK_INPUT_DEFAULTS = {
  backgroundColor: DECK_COLOR_SURFACE,
  borderColor: DECK_COLOR_BORDER,
  borderWidth: 1,
  /** Paridade de moldura com gráfico/KPI — mesma curva → mesma leitura da sombra. */
  borderRadius: 16,
  boxShadow:
    "0 1px 2px rgba(15, 23, 42, 0.06), 0 12px 28px rgba(15, 23, 42, 0.10)",
  controlFill: DECK_COLOR_SURFACE,
  controlBorderColor: DECK_COLOR_SHAPE_STROKE,
  controlBorderWidth: 1,
  controlBorderRadius: 6,
} as const;

/** Defaults de tabela — células (grade) vs moldura (chrome alinhado a KPI/gráfico). */
export const DECK_TABLE_DEFAULTS = {
  headerBg: DECK_COLOR_TABLE_HEADER_BG,
  headerTextColor: DECK_COLOR_MUTED,
  cellBg: DECK_COLOR_TABLE_CELL_BG,
  cellTextColor: DECK_COLOR_TABLE_CELL_TEXT,
  /** Bordas entre células (grade interna — mais suave que o contorno do bloco). */
  borderColor: DECK_COLOR_TABLE_BORDER,
  /** Fundo da moldura (`tableParts.frame`) — superfície Office. */
  frameFill: DECK_COLOR_SURFACE,
  /** Contorno da moldura — mesmo `#b4b4b4` de gráfico/KPI (`DECK_COLOR_BORDER`). */
  frameStroke: DECK_COLOR_BORDER,
  /** Raio padrão da moldura (px) — paridade com KPI/gráfico. */
  borderRadius: 16,
  borderWidth: 1,
  /**
   * Sombra padrão da moldura (contato + ambiente).
   * Persistida em `tableParts.frame.style.boxShadow` e/ou `block.style.boxShadow`.
   */
  boxShadow:
    "0 1px 2px rgba(15, 23, 42, 0.06), 0 12px 28px rgba(15, 23, 42, 0.10)",
} as const;

/**
 * CSS custom properties para o bloco de dados TV.
 * Aplicar no host (`.tdp-data-block` / presentation root) para herança.
 */
export function deckDataBlockCssVars(theme: DeckColorTheme = DECK_THEME_LIGHT): Record<string, string> {
  return {
    "--tdp-data-bg": theme.bg,
    "--tdp-data-surface": theme.bg,
    "--tdp-data-text": theme.text,
    "--tdp-data-text-strong": theme.textStrong,
    "--tdp-data-muted": theme.muted,
    "--tdp-data-accent": theme.accent,
    "--tdp-data-border": theme.border,
    "--delpi-ui-accent": theme.accent,
    "--delpi-ui-surface": theme.bg,
    "--delpi-ui-text": theme.textStrong,
    "--delpi-ui-muted": theme.muted,
    "--delpi-ui-border": theme.border,
  };
}

/** Aliases históricos (gráficos Office) — preferir DECK_* em código novo. */
export const OFFICE_CHART_SERIES_COLOR = DECK_COLOR_ACCENT;
export const OFFICE_CHART_AREA_FILL = DECK_COLOR_SURFACE;
export const OFFICE_CHART_AREA_STROKE = DECK_COLOR_BORDER;
export const OFFICE_CHART_PLOT_FILL = DECK_COLOR_SURFACE;
export const OFFICE_CHART_PLOT_STROKE = DECK_COLOR_BORDER;
