/** Paleta alinhada ao portal (`--primary`, `--secundary`, `--success`, `--danger`). */
export const CHART_COLORS = {
  primary: "#089bdb",
  secondary: "#003866",
  success: "#067647",
  warning: "#f59e0b",
  danger: "#b42318",
  muted: "#94a3b8",
} as const;

export const SENSO_COLORS = [
  "#089bdb",
  "#003866",
  "#067647",
  "#f59e0b",
  "#7b1fa2",
] as const;

export const NC_STATUS_COLORS: Record<string, string> = {
  open: "#f59e0b",
  in_progress: "#089bdb",
  closed: "#067647",
};

export const CHART_HEIGHT = 300;
export const CHART_FONT_SIZE = 13;
export const AXIS_TICK = { fontSize: CHART_FONT_SIZE };
export const TOOLTIP_STYLE = { fontSize: CHART_FONT_SIZE };

export const REFERENCE_LINE_100 = {
  y: 100 as const,
  stroke: CHART_COLORS.secondary,
  strokeDasharray: "4 4",
  strokeOpacity: 0.35,
};
