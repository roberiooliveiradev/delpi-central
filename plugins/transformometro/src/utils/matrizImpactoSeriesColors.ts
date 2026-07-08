/** Paleta estável para séries (melhorias) no scatter do processo. */
export const MATRIZ_SERIES_COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#8b5cf6",
  "#ef4444",
  "#06b6d4",
  "#ec4899",
  "#84cc16",
] as const;

export function matrizSeriesColor(colorIndex?: number | null): string | undefined {
  if (colorIndex == null || Number.isNaN(colorIndex)) return undefined;
  return MATRIZ_SERIES_COLORS[((colorIndex % MATRIZ_SERIES_COLORS.length) + MATRIZ_SERIES_COLORS.length) % MATRIZ_SERIES_COLORS.length];
}
