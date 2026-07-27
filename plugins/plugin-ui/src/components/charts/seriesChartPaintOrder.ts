/**
 * Ordem de pintura de séries sobrepostas (área / fills).
 * Em SVG o último desenho fica na frente — séries menores por cima
 * preservam a cor da legenda sem a maior “lavar” as demais.
 */

export type SeriesPaintMagnitudeSource = {
  points: ReadonlyArray<{ value?: number | null }>;
};

/** Magnitude típica da série (média dos |valores| finitos). */
export function seriesPaintMagnitude(series: SeriesPaintMagnitudeSource): number {
  let sum = 0;
  let count = 0;
  for (const point of series.points) {
    if (point.value == null) continue;
    const raw = Number(point.value);
    if (!Number.isFinite(raw)) continue;
    sum += Math.abs(raw);
    count += 1;
  }
  return count > 0 ? sum / count : 0;
}

/**
 * Índices na ordem de pintura (fundo → frente): maior magnitude primeiro.
 * Empate: índice original (estável).
 * Cores / `seriesIndex` de interação continuam no índice original da lista.
 */
export function orderSeriesIndicesForOverlappingPaint(
  seriesList: ReadonlyArray<SeriesPaintMagnitudeSource>,
): number[] {
  return seriesList
    .map((_, index) => index)
    .sort((a, b) => {
      const delta =
        seriesPaintMagnitude(seriesList[b]!) - seriesPaintMagnitude(seriesList[a]!);
      if (delta !== 0) return delta;
      return a - b;
    });
}
