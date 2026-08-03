/** Curva Catmull-Rom densificada para linhas/áreas de série (SVG polyline/polygon). */

export type SeriesChartCurvePoint = { x: number; y: number };

const DEFAULT_SEGMENTS_PER_SPAN = 12;

/**
 * Catmull-Rom pode ultrapassar os âncoras (overshoot). Sem clamp, o path fura o
 * clipPath → área «cortada» no topo / «vazando» nas laterais (linhas suaves).
 */
export function clampSeriesChartCurveToAnchors(
  densified: ReadonlyArray<SeriesChartCurvePoint>,
  anchors: ReadonlyArray<SeriesChartCurvePoint>,
): SeriesChartCurvePoint[] {
  if (anchors.length === 0) return densified.map((point) => ({ ...point }));
  let minX = anchors[0]!.x;
  let maxX = anchors[0]!.x;
  let minY = anchors[0]!.y;
  let maxY = anchors[0]!.y;
  for (let i = 1; i < anchors.length; i += 1) {
    const point = anchors[i]!;
    if (point.x < minX) minX = point.x;
    if (point.x > maxX) maxX = point.x;
    if (point.y < minY) minY = point.y;
    if (point.y > maxY) maxY = point.y;
  }
  return densified.map((point) => ({
    x: Math.min(maxX, Math.max(minX, point.x)),
    y: Math.min(maxY, Math.max(minY, point.y)),
  }));
}

/**
 * Densifica âncoras com Catmull-Rom → segmentos retos curtos (aparência suave).
 * Com menos de 3 pontos, devolve os âncoras (sem suavização).
 * Pontos densificados são clamados à caixa dos âncoras (sem overshoot no clip).
 */
export function densifySeriesChartCurve(
  anchors: ReadonlyArray<SeriesChartCurvePoint>,
  segmentsPerSpan = DEFAULT_SEGMENTS_PER_SPAN,
): SeriesChartCurvePoint[] {
  if (anchors.length < 2) return anchors.map((point) => ({ ...point }));
  if (anchors.length === 2 || segmentsPerSpan < 1) {
    return anchors.map((point) => ({ ...point }));
  }

  const points: SeriesChartCurvePoint[] = [];
  const n = anchors.length;
  for (let i = 0; i < n - 1; i += 1) {
    const p0 = anchors[Math.max(0, i - 1)]!;
    const p1 = anchors[i]!;
    const p2 = anchors[i + 1]!;
    const p3 = anchors[Math.min(n - 1, i + 2)]!;
    for (let s = 0; s < segmentsPerSpan; s += 1) {
      const t = s / segmentsPerSpan;
      const t2 = t * t;
      const t3 = t2 * t;
      points.push({
        x:
          0.5 *
          (2 * p1.x +
            (-p0.x + p2.x) * t +
            (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 +
            (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3),
        y:
          0.5 *
          (2 * p1.y +
            (-p0.y + p2.y) * t +
            (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 +
            (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3),
      });
    }
  }
  points.push({ ...anchors[n - 1]! });
  return clampSeriesChartCurveToAnchors(points, anchors);
}

export function seriesChartPointsAttr(points: ReadonlyArray<SeriesChartCurvePoint>): string {
  return points.map((point) => `${point.x},${point.y}`).join(" ");
}

/** Resolve pontos do traço: retos (ângulos) ou densificados (suaves). */
export function resolveSeriesChartStrokePoints(
  anchors: ReadonlyArray<SeriesChartCurvePoint>,
  smooth: boolean,
): SeriesChartCurvePoint[] {
  if (!smooth || anchors.length < 3) {
    return anchors.map((point) => ({ ...point }));
  }
  return densifySeriesChartCurve(anchors);
}
