/** Tokens Recharts — legível em claro e escuro (usa variáveis CSS do plugin). */

export const CHART_AXIS_TICK = {
  fontSize: 12,
  fill: "var(--pac-chart-tick)",
} as const;

export const CHART_AXIS_TICK_SM = {
  fontSize: 11,
  fill: "var(--pac-chart-tick)",
} as const;

export const CHART_TOOLTIP_PROPS = {
  contentStyle: {
    borderRadius: 12,
    border: "1px solid var(--pac-card-border)",
    background: "var(--pac-card-bg)",
    color: "var(--pac-text)",
  },
  labelStyle: {
    color: "var(--pac-text)",
    fontWeight: 600,
  },
  itemStyle: {
    color: "var(--pac-text-muted)",
  },
} as const;

export const CHART_LEGEND_PROPS = {
  wrapperStyle: {
    color: "var(--pac-text-muted)",
    fontSize: 12,
  },
} as const;
