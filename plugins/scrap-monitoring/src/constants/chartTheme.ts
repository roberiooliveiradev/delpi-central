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

export const CHART_RANKING_HEIGHT = 280;

/** Largura do eixo Y em gráficos de barra horizontais (cards full-width). */
export const CHART_Y_AXIS_WIDTH = 260;

export const CHART_AXIS_TICK = {
  fontSize: 12,
  fill: "var(--sm-chart-axis)",
} as const;

export const CHART_GRID_STROKE = "var(--sm-chart-grid)";
