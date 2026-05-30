export const CHART_COLORS = {
  primary: "#089bdb",
  secondary: "#003866",
  success: "#2e7d32",
  warning: "#f9a825",
  danger: "#c62828",
  muted: "#94a3b8",
} as const;

export const SENSO_COLORS = [
  "#089bdb",
  "#003866",
  "#2e7d32",
  "#f9a825",
  "#7b1fa2",
] as const;

export const NC_STATUS_COLORS: Record<string, string> = {
  open: "#f9a825",
  in_progress: "#089bdb",
  closed: "#2e7d32",
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
