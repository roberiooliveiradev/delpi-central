/** Paleta alinhada ao portal (`--primary`, `--secundary`, `--chart-*`). */
export const CHART_COLORS = {
  primary: "#089bdb",
  secondary: "#003866",
  accent: "#7e14ff",
  muted: "#64748b",
} as const;

export const PIE_COLORS = [
  "#089bdb",
  "#003866",
  "#0ea5e9",
  "#6366f1",
  "#14b8a6",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#22c55e",
  "#64748b",
] as const;

export const CHART_RANKING_HEIGHT = 300;
/** Ranking de produtos full-width — mais altura por barra. */
export const CHART_PRODUCT_RANKING_HEIGHT = 380;
export const CHART_MOTIVO_HEIGHT = 300;
export const CHART_SERIES_HEIGHT = 300;

/** Rosca Motivo — raios do Pie. */
export const CHART_MOTIVO_INNER_RADIUS = 58;
export const CHART_MOTIVO_OUTER_RADIUS = 98;

/** Eixo Y — half-width (CT / colaborador). */
export const CHART_Y_AXIS_WIDTH = 160;
/** Eixo Y — full-width com código + descrição em 2 linhas. */
export const CHART_PRODUCT_Y_AXIS_WIDTH = 340;

export const CHART_AXIS_TICK = {
  fontSize: 12,
  fill: "var(--sm-chart-axis)",
} as const;

export const CHART_GRID_STROKE = "var(--sm-chart-grid)";
