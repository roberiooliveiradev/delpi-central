/** Paleta departamental padrão (8 dashboards DELPI). */
export const CHART_COLORS_DEPARTMENTAL = [
  "#089bdb",
  "#003866",
  "#47bfff",
  "#7e14ff",
  "#2e7d32",
  "#f2a100",
] as const;

/** Paleta enxuta do dashboard LMPs. */
export const CHART_COLORS_LMPS = ["#1d8cf8", "#f97316", "#1e40af"] as const;

/** Paleta com tokens CSS (temas claro/escuro — ex.: PAC). */
export const CHART_COLORS_CSS_VARS = [
  "var(--chart-1, #089bdb)",
  "var(--chart-2, #003866)",
  "var(--chart-3, #47bfff)",
  "var(--chart-4, #7e14ff)",
  "var(--chart-5, #2e7d32)",
  "var(--chart-6, #f2a100)",
] as const;

export const CHART_HEIGHT_DEFAULT = 280;

export type ChartColorPalette = readonly string[];

/** @deprecated Use `CHART_COLORS_DEPARTMENTAL` ou alias local `CHART_COLORS`. */
export const CHART_COLORS = CHART_COLORS_DEPARTMENTAL;

export const CHART_HEIGHT = CHART_HEIGHT_DEFAULT;
