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
export const CHART_PRODUCT_RANKING_HEIGHT = 380;
export const CHART_MOTIVO_HEIGHT_MIN = 260;
export const CHART_MOTIVO_HEIGHT_MAX = 560;
export const CHART_MOTIVO_HEIGHT_BASE = 200;
export const CHART_MOTIVO_HEIGHT_PER_ITEM = 30;
export const CHART_SERIES_HEIGHT_MIN = 260;

/** Rosca Motivo — raios default (escalados em runtime). */
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

/** Altura do card Motivo cresce com a quantidade de itens na legenda. */
export function resolveMotivoChartHeight(itemCount: number): number {
  const count = Math.max(0, Math.floor(itemCount));
  const raw = CHART_MOTIVO_HEIGHT_BASE + count * CHART_MOTIVO_HEIGHT_PER_ITEM;
  return Math.min(
    CHART_MOTIVO_HEIGHT_MAX,
    Math.max(CHART_MOTIVO_HEIGHT_MIN, raw),
  );
}

/** Escala a rosca proporcional à altura disponível. */
export function resolveMotivoPieRadii(height: number): {
  innerRadius: number;
  outerRadius: number;
} {
  const outer = Math.min(
    CHART_MOTIVO_OUTER_RADIUS + 20,
    Math.max(CHART_MOTIVO_OUTER_RADIUS - 16, Math.floor(height * 0.3)),
  );
  const inner = Math.max(36, Math.floor(outer * 0.58));
  return { innerRadius: inner, outerRadius: outer };
}

/** Altura de barras horizontais conforme nº de categorias. */
export function resolveRankingChartHeight(
  itemCount: number,
  variant: "simple" | "product" = "simple",
): number {
  const count = Math.max(1, Math.floor(itemCount));
  const row = variant === "product" ? 38 : 32;
  const padding = variant === "product" ? 88 : 72;
  const min = variant === "product" ? 280 : 240;
  const max = variant === "product" ? 520 : 420;
  return Math.min(max, Math.max(min, padding + count * row));
}
