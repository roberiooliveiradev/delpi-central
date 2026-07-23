import type {
  ComunicadoConnectorRouting,
  ComunicadoGeometryVertex,
  ComunicadoShapeConnector,
} from "./comunicadoTypes";

export type ConnectorAnchorId = NonNullable<ComunicadoShapeConnector["fromAnchor"]>;

const ROUTINGS = new Set<ComunicadoConnectorRouting>(["straight", "elbow", "curve"]);

export function normalizeConnectorRouting(value: unknown): ComunicadoConnectorRouting {
  if (typeof value === "string" && ROUTINGS.has(value as ComunicadoConnectorRouting)) {
    return value as ComunicadoConnectorRouting;
  }
  return "straight";
}

/**
 * Conector angulado (elbow): caminho ortogonal H-V-H ou V-H-V
 * preferindo a direção da âncora de origem.
 */
export function buildElbowRoutePoints(
  start: ComunicadoGeometryVertex,
  end: ComunicadoGeometryVertex,
  fromAnchor: ConnectorAnchorId = "center",
  toAnchor: ConnectorAnchorId = "center",
): ComunicadoGeometryVertex[] {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const preferHorizontal =
    fromAnchor === "e" ||
    fromAnchor === "w" ||
    toAnchor === "e" ||
    toAnchor === "w" ||
    (fromAnchor === "center" && toAnchor === "center" && Math.abs(dx) >= Math.abs(dy));

  if (preferHorizontal) {
    const midX = start.x + dx / 2;
    if (Math.abs(dy) < 0.05) {
      return [start, end];
    }
    return [start, { x: midX, y: start.y }, { x: midX, y: end.y }, end];
  }

  const midY = start.y + dy / 2;
  if (Math.abs(dx) < 0.05) {
    return [start, end];
  }
  return [start, { x: start.x, y: midY }, { x: end.x, y: midY }, end];
}

/** Ponto de controle da curva (meio + offset perpendicular ~25% do comprimento). */
export function buildCurveControlPoint(
  start: ComunicadoGeometryVertex,
  end: ComunicadoGeometryVertex,
): ComunicadoGeometryVertex {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const len = Math.hypot(dx, dy) || 1;
  const offset = len * 0.25;
  return {
    x: (start.x + end.x) / 2 + (-dy / len) * offset,
    y: (start.y + end.y) / 2 + (dx / len) * offset,
  };
}

/**
 * Vértices persistidos conforme roteamento.
 * Curve guarda só endpoints (controle derivado na renderização).
 */
export function buildRoutedLinePoints(
  start: ComunicadoGeometryVertex,
  end: ComunicadoGeometryVertex,
  routing: ComunicadoConnectorRouting = "straight",
  fromAnchor: ConnectorAnchorId = "center",
  toAnchor: ConnectorAnchorId = "center",
): ComunicadoGeometryVertex[] {
  if (routing === "elbow") {
    return buildElbowRoutePoints(start, end, fromAnchor, toAnchor);
  }
  return [start, end];
}
