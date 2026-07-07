/** Paleta alinhada ao portal (`--primary`, `--secundary`, `--chart-*`). */
export const CHART_COLORS = {
  primary: "#089bdb",
  secondary: "#003866",
  accent: "#7e14ff",
  muted: "#64748b",
} as const;

export const CHART_HEIGHT = 340;
export const CHART_RANKING_HEIGHT = 320;
/** Altura dos gráficos na visão expandida (modal). */
export const CHART_EXPANDED_HEIGHT = 700;
export const CHART_FONT_SIZE = 13;

export const CHART_AXIS_TICK = {
  fontSize: CHART_FONT_SIZE,
  fill: "var(--cr-chart-axis)",
} as const;

export const LABEL_LIST_STYLE = {
  fontSize: CHART_FONT_SIZE,
  fill: "var(--cr-chart-label)",
} as const;

export const CHART_GRID_STROKE = "var(--cr-chart-grid)";
