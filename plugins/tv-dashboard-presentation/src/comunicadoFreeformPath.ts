/**
 * Suavização / simplificação de caminhos livres (curva, polilinha, rabisco).
 */

import type { ComunicadoGeometryVertex } from "./comunicadoTypes";

function dist(a: ComunicadoGeometryVertex, b: ComunicadoGeometryVertex): number {
  return Math.hypot(b.x - a.x, b.y - a.y);
}

/** Douglas–Peucker leve para rabiscos densos. */
export function simplifyPolyline(
  points: ComunicadoGeometryVertex[],
  tolerancePct = 0.35,
): ComunicadoGeometryVertex[] {
  if (points.length <= 2) return points.map((point) => ({ ...point }));

  const sqTol = tolerancePct * tolerancePct;

  function perpendicularDistanceSq(
    point: ComunicadoGeometryVertex,
    start: ComunicadoGeometryVertex,
    end: ComunicadoGeometryVertex,
  ): number {
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    if (dx === 0 && dy === 0) {
      return (point.x - start.x) ** 2 + (point.y - start.y) ** 2;
    }
    const t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / (dx * dx + dy * dy);
    const projX = start.x + t * dx;
    const projY = start.y + t * dy;
    return (point.x - projX) ** 2 + (point.y - projY) ** 2;
  }

  function simplifySection(
    source: ComunicadoGeometryVertex[],
    startIndex: number,
    endIndex: number,
    out: ComunicadoGeometryVertex[],
  ): void {
    let maxDist = 0;
    let index = startIndex;
    for (let i = startIndex + 1; i < endIndex; i += 1) {
      const d = perpendicularDistanceSq(source[i]!, source[startIndex]!, source[endIndex]!);
      if (d > maxDist) {
        maxDist = d;
        index = i;
      }
    }
    if (maxDist > sqTol && index > startIndex && index < endIndex) {
      simplifySection(source, startIndex, index, out);
      out.pop();
      simplifySection(source, index, endIndex, out);
      return;
    }
    out.push(source[startIndex]!, source[endIndex]!);
  }

  const result: ComunicadoGeometryVertex[] = [];
  simplifySection(points, 0, points.length - 1, result);
  /* Remover duplicatas consecutivas do merge. */
  const deduped: ComunicadoGeometryVertex[] = [result[0]!];
  for (let i = 1; i < result.length; i += 1) {
    const prev = deduped[deduped.length - 1]!;
    const cur = result[i]!;
    if (Math.hypot(cur.x - prev.x, cur.y - prev.y) > 1e-6) {
      deduped.push(cur);
    }
  }
  return deduped;
}

/**
 * Catmull-Rom → pontos densos (curva suave a partir dos cliques).
 */
export function smoothCurveThroughPoints(
  anchors: ComunicadoGeometryVertex[],
  segmentsPerSpan = 8,
): ComunicadoGeometryVertex[] {
  if (anchors.length < 2) return anchors.map((point) => ({ ...point }));
  if (anchors.length === 2) return [anchors[0]!, anchors[1]!];

  const points: ComunicadoGeometryVertex[] = [];
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
  points.push(anchors[n - 1]!);
  return points;
}

export function pathLength(points: ComunicadoGeometryVertex[]): number {
  let total = 0;
  for (let i = 1; i < points.length; i += 1) {
    total += dist(points[i - 1]!, points[i]!);
  }
  return total;
}
