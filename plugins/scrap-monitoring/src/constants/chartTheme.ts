/** Paleta alinhada ao portal (`--primary`, `--secundary`, `--chart-*`). */
export const CHART_COLORS = {
  primary: "#089bdb",
  secondary: "#003866",
  accent: "#7e14ff",
  muted: "#64748b",
} as const;

/**
 * Paleta categórica da rosca Motivo — hues intercalados (não uma rampa de azul).
 * Os primeiros índices são os fatias maiores do ranking.
 */
export const PIE_COLORS = [
  "#089bdb",
  "#f59e0b",
  "#16a34a",
  "#e11d48",
  "#7c3aed",
  "#ea580c",
  "#0d9488",
  "#2563eb",
  "#ca8a04",
  "#db2777",
  "#65a30d",
  "#78716c",
] as const;

function hashPieKey(value: string): number {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) | 0;
  }
  return Math.abs(hash);
}

/** Uma cor por fatia, estável pelo código do motivo e sem repetir na mesma rosca. */
export function assignDistinctPieColors(keys: string[]): string[] {
  const used = new Set<number>();
  const paletteSize = PIE_COLORS.length;
  const probeStep = 5;

  return keys.map((raw, index) => {
    const key = raw.trim().toUpperCase() || `idx:${index}`;
    let slot = hashPieKey(key) % paletteSize;
    let attempts = 0;
    while (used.has(slot) && attempts < paletteSize) {
      slot = (slot + probeStep) % paletteSize;
      attempts += 1;
    }
    if (used.has(slot)) {
      slot = index % paletteSize;
    }
    used.add(slot);
    return PIE_COLORS[slot];
  });
}

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
