/**
 * Criação de linhas/conectores a partir de gesto de desenho no palco (Google Slides).
 */

import type {
  ComunicadoBlock,
  ComunicadoConnectorRouting,
  ComunicadoGeometryVertex,
  ComunicadoShapeBlock,
  ComunicadoShapeKind,
} from "./comunicadoTypes";
import type { ComunicadoLineToolId } from "./comunicadoShapeCatalog";
import { findNearestConnectionSite } from "./comunicadoConnectionSites";
import {
  applyConnectorGeometry,
  normalizeConnectorAnchor,
  type ComunicadoConnectorAnchor,
} from "./comunicadoConnectors";
import {
  buildCurveControlPoint,
  buildRoutedLinePoints,
} from "./comunicadoConnectorRouting";
import {
  applyLinePolyline,
  geometryBoundingFrame,
} from "./comunicadoShapeGeometry";

export type LineDrawToolKind = Extract<
  ComunicadoLineToolId,
  "line" | "line-arrow" | "elbow-connector" | "curved-connector"
>;

export function lineToolShapeKind(tool: LineDrawToolKind): ComunicadoShapeKind {
  if (tool === "line-arrow" || tool === "elbow-connector" || tool === "curved-connector") {
    return "line-arrow-right";
  }
  return "line";
}

export function lineToolRouting(tool: LineDrawToolKind): ComunicadoConnectorRouting {
  if (tool === "elbow-connector") return "elbow";
  if (tool === "curved-connector") return "curve";
  return "straight";
}

export function isLineDrawToolId(value: string | null | undefined): value is LineDrawToolKind {
  return (
    value === "line" ||
    value === "line-arrow" ||
    value === "elbow-connector" ||
    value === "curved-connector"
  );
}

function newLineId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `line-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export type DrawnLineAttach = {
  blockId: string;
  anchor: ComunicadoConnectorAnchor;
};

/** Amostra curva quadrática para persistir sem `connector.routing` (linha livre). */
export function sampleQuadraticCurve(
  start: ComunicadoGeometryVertex,
  end: ComunicadoGeometryVertex,
  samples = 16,
): ComunicadoGeometryVertex[] {
  const control = buildCurveControlPoint(start, end);
  const points: ComunicadoGeometryVertex[] = [];
  for (let i = 0; i <= samples; i += 1) {
    const t = i / samples;
    const u = 1 - t;
    points.push({
      x: u * u * start.x + 2 * u * t * control.x + t * t * end.x,
      y: u * u * start.y + 2 * u * t * control.y + t * t * end.y,
    });
  }
  return points;
}

/** Preview de pontos durante o gesto. */
export function previewDrawnLinePoints(
  start: ComunicadoGeometryVertex,
  end: ComunicadoGeometryVertex,
  tool: LineDrawToolKind,
  fromAnchor: ComunicadoConnectorAnchor = "center",
  toAnchor: ComunicadoConnectorAnchor = "center",
): ComunicadoGeometryVertex[] {
  const routing = lineToolRouting(tool);
  if (routing === "curve") {
    return sampleQuadraticCurve(start, end);
  }
  return buildRoutedLinePoints(start, end, routing, fromAnchor, toAnchor);
}

export function snapPointToConnectionSite(
  point: ComunicadoGeometryVertex,
  blocks: ComunicadoBlock[],
  excludeBlockIds?: ReadonlySet<string>,
): { point: ComunicadoGeometryVertex; attach?: DrawnLineAttach } {
  const site = findNearestConnectionSite(point, blocks, { excludeBlockIds });
  if (!site) return { point };
  return {
    point: { x: site.x, y: site.y },
    attach: { blockId: site.blockId, anchor: normalizeConnectorAnchor(site.id) },
  };
}

export function createDrawnLineBlock(params: {
  tool: LineDrawToolKind;
  start: ComunicadoGeometryVertex;
  end: ComunicadoGeometryVertex;
  blocks: ComunicadoBlock[];
  zIndex?: number;
  fromAttach?: DrawnLineAttach;
  toAttach?: DrawnLineAttach;
}): ComunicadoShapeBlock {
  const shape = lineToolShapeKind(params.tool);
  const routing = lineToolRouting(params.tool);
  const fromAnchor = params.fromAttach?.anchor ?? "center";
  const toAnchor = params.toAttach?.anchor ?? "center";
  const hasAttach = Boolean(params.fromAttach || params.toAttach);

  let routePoints: ComunicadoGeometryVertex[];
  if (routing === "curve" && hasAttach) {
    routePoints = [params.start, params.end];
  } else if (routing === "curve") {
    routePoints = sampleQuadraticCurve(params.start, params.end);
  } else {
    routePoints = buildRoutedLinePoints(
      params.start,
      params.end,
      routing,
      fromAnchor,
      toAnchor,
    );
  }

  let draft: ComunicadoShapeBlock = {
    id: newLineId(),
    type: "shape",
    shape,
    frame: geometryBoundingFrame({ primitive: "line", points: routePoints }),
    style: {
      zIndex: params.zIndex ?? 2,
      stroke: "#089bdb",
      strokeWidth: 3,
      fill: "transparent",
    },
    content: "",
  };
  draft = applyLinePolyline(draft, routePoints);

  if (hasAttach) {
    draft = {
      ...draft,
      connector: {
        ...(params.fromAttach
          ? { fromBlockId: params.fromAttach.blockId, fromAnchor: params.fromAttach.anchor }
          : {}),
        ...(params.toAttach
          ? { toBlockId: params.toAttach.blockId, toAnchor: params.toAttach.anchor }
          : {}),
        ...(routing !== "straight" ? { routing } : {}),
      },
    };
    draft = applyConnectorGeometry(draft, [...params.blocks, draft]);
  }

  return draft;
}
