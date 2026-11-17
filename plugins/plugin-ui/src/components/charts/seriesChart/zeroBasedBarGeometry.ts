/** Geometria de colunas/barras com a origem no valor ZERO, não no mínimo do eixo.
 *
 * Em domínios mistos (ex.: -781 mil a +85 mil), usar a borda inferior do
 * plot como início das barras falsifica visualmente todos os negativos.
 * A escala de valor já inclui 0 via resolveSeriesChartValueDomain.
 */
export type ZeroBasedValueSpan = {
  start: number;
  size: number;
  zero: number;
  end: number;
};

export function resolveZeroBasedValueSpan(
  toPixel: (value: number) => number,
  value: number,
): ZeroBasedValueSpan {
  const zero = toPixel(0);
  const end = toPixel(value);
  return {
    start: Math.min(zero, end),
    size: Math.abs(end - zero),
    zero,
    end,
  };
}

/** Área de clique mínima sem inverter nem falsificar a polaridade da barra. */
export function ensureSelectableBarSpan(
  span: ZeroBasedValueSpan,
  value: number,
  minSize: number,
  reversedAxis = false,
): { start: number; size: number } {
  if (span.size >= minSize) return { start: span.start, size: span.size };
  const goesTowardHigherPixel = reversedAxis ? value > 0 : value < 0;
  return {
    start: goesTowardHigherPixel ? span.zero : span.zero - minSize,
    size: minSize,
  };
}
