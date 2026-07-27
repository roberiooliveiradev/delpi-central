/** Curva Catmull-Rom densificada para linhas/áreas de série (SVG polyline/polygon). */

export type SeriesChartCurvePoint = { x: number; y: number };

const DEFAULT_SEGMENTS_PER_SPAN = 12;

/**
 * Densifica âncoras com Catmull-Rom → segmentos retos curtos (aparência suave).
 * Com menos de 3 pontos, devolve os âncoras (sem suavização).
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
  return points;
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
