export const CHART_COLORS = {
  primary: "#089bdb",
  secondary: "#003866",
  success: "#2e7d32",
  warning: "#f9a825",
  danger: "#c62828",
  muted: "#94a3b8",
  planned: "#64748b",
} as const;

/** Cores do gráfico de eficiência por CT. */
export function getEfficiencyByCtBarColor(pct: number): string {
  if (pct >= 100) return CHART_COLORS.success;
  if (pct >= 90) return CHART_COLORS.warning;
  return CHART_COLORS.danger;
}

export const CHART_HEIGHT = 320;
/** Altura padrão dos gráficos na visão expandida (modal). */
export const CHART_EXPANDED_HEIGHT = 700;
export const CHART_FONT_SIZE = 13;

export const AXIS_TICK = { fontSize: CHART_FONT_SIZE };
export const TOOLTIP_STYLE = { fontSize: CHART_FONT_SIZE };

/** Linha de referência em 100% nos gráficos de eficiência. */
export const REFERENCE_LINE_100 = {
  y: 100 as const,
  stroke: CHART_COLORS.secondary,
  strokeDasharray: "4 4",
  strokeOpacity: 0.4,
  label: {
    value: "100%",
    position: "insideTopRight" as const,
    fontSize: 12,
    fill: CHART_COLORS.secondary,
    fillOpacity: 0.55,
  },
};
