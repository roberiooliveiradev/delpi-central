import type { CSSProperties } from "react";

import type {
  ComunicadoBlock,
  ComunicadoFrame,
  ComunicadoGeometryVertex,
  ComunicadoShapeBlock,
} from "./comunicadoTypes";
import {
  isLineShapeKind,
  isPointShapeKind,
  resolveShapePrimitive,
  type ComunicadoVisualPrimitive,
} from "./comunicadoVisualPrimitive";

export type { ComunicadoGeometryVertex } from "./comunicadoTypes";

/**
 * Geometria canônica derivada do primitivo:
 * - ponto: posição sem dimensão (0D)
 * - linha: polilinha aberta com ≥ 2 pontos
 * - área (forma): polígono fechado com ≥ 3 pontos (arestas = segmentos entre vértices)
 */
export type ComunicadoShapeGeometry =
  | { primitive: "point"; position: ComunicadoGeometryVertex }
  | { primitive: "line"; points: ComunicadoGeometryVertex[] }
  | { primitive: "area"; points: ComunicadoGeometryVertex[] };

export const COMUNICADO_MARKER_RADIUS_DEFAULT = 6;
/** Alvo mínimo de seleção no editor (% do palco). */
export const COMUNICADO_POINT_HIT_SIZE_PCT = 2;
/**
 * Padding da bbox de linha (% do palco) — espaço para espessura + ponta da seta.
 * Sem isso, linha horizontal colapsa em h≈0,5% e a seta some com `preserveAspectRatio="none"`.
 */
export const COMUNICADO_LINE_VISUAL_PAD_PCT = 2;

export function minimumVertexCount(primitive: ComunicadoVisualPrimitive): number {
  if (primitive === "point") return 1;
  if (primitive === "line") return 2;
  return 3;
}

function lineEndpointsFromFrame(frame: ComunicadoFrame): ComunicadoGeometryVertex[] {
  const y = frame.y + frame.h / 2;
  return [
    { x: frame.x, y },
    { x: frame.x + frame.w, y },
  ];
}

function areaPolygonFromFrame(frame: ComunicadoFrame): ComunicadoGeometryVertex[] {
  const { x, y, w, h } = frame;
  return [
    { x, y },
    { x: x + w, y },
    { x: x + w, y: y + h },
    { x, y: y + h },
  ];
}

function resolvePointPosition(block: ComunicadoShapeBlock): ComunicadoGeometryVertex {
  // Frame canônico do ponto (w=h=0): posição = frame.x/y (drag atualiza o frame).
  if (block.frame.w === 0 && block.frame.h === 0) {
    return { x: block.frame.x, y: block.frame.y };
  }
  if (block.vertices?.[0]) return block.vertices[0];
  return {
    x: block.frame.x + block.frame.w / 2,
    y: block.frame.y + block.frame.h / 2,
  };
}

export function resolveShapeGeometry(block: ComunicadoShapeBlock): ComunicadoShapeGeometry {
  const primitive = resolveShapePrimitive(block.shape);

  if (primitive === "point") {
    return { primitive: "point", position: resolvePointPosition(block) };
  }

  if (primitive === "line") {
    const points =
      block.vertices && block.vertices.length >= 2
        ? block.vertices
        : lineEndpointsFromFrame(block.frame);
    return { primitive: "line", points };
  }

  const points =
    block.vertices && block.vertices.length >= 3
      ? block.vertices
      : areaPolygonFromFrame(block.frame);
  return { primitive: "area", points };
}

/** Caixa de seleção / interseção — derivada da geometria, não da dimensão do ponto. */
export function geometryBoundingFrame(geometry: ComunicadoShapeGeometry): ComunicadoFrame {
  if (geometry.primitive === "point") {
    const half = COMUNICADO_POINT_HIT_SIZE_PCT / 2;
    const { x, y } = geometry.position;
    return { x: x - half, y: y - half, w: COMUNICADO_POINT_HIT_SIZE_PCT, h: COMUNICADO_POINT_HIT_SIZE_PCT };
  }

  const xs = geometry.points.map((point) => point.x);
  const ys = geometry.points.map((point) => point.y);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const maxX = Math.max(...xs);
  const maxY = Math.max(...ys);
  const rawW = Math.max(0, maxX - minX);
  const rawH = Math.max(0, maxY - minY);

  if (geometry.primitive === "line") {
    const pad = COMUNICADO_LINE_VISUAL_PAD_PCT;
    return {
      x: minX - pad,
      y: minY - pad,
      w: Math.max(0.5, rawW) + 2 * pad,
      h: Math.max(0.5, rawH) + 2 * pad,
    };
  }

  return {
    x: minX,
    y: minY,
    w: Math.max(0.5, rawW),
    h: Math.max(0.5, rawH),
  };
}

/** Frame persistido: ponto só posição (w=h=0); demais primitivos usam bbox da geometria. */
export function geometryToPersistedFrame(block: ComunicadoShapeBlock): ComunicadoFrame {
  const geometry = resolveShapeGeometry(block);
  if (geometry.primitive === "point") {
    return { x: geometry.position.x, y: geometry.position.y, w: 0, h: 0 };
  }
  return geometryBoundingFrame(geometry);
}

export function shapeBlockAllowsResize(block: ComunicadoShapeBlock): boolean {
  return !isPointShapeKind(block.shape);
}

export function clampFrameForShapeBlock(block: ComunicadoShapeBlock, frame: ComunicadoFrame): ComunicadoFrame {
  if (isPointShapeKind(block.shape)) {
    return {
      x: Math.max(0, Math.min(100, frame.x)),
      y: Math.max(0, Math.min(100, frame.y)),
      w: 0,
      h: 0,
    };
  }

  if (isLineShapeKind(block.shape)) {
    return {
      x: Math.max(0, Math.min(100 - frame.w, frame.x)),
      y: Math.max(0, Math.min(100 - frame.h, frame.y)),
      w: Math.max(1, Math.min(100, frame.w)),
      h: Math.max(0.5, Math.min(100, frame.h)),
    };
  }

  return {
    x: Math.max(0, Math.min(100 - frame.w, frame.x)),
    y: Math.max(0, Math.min(100 - frame.h, frame.y)),
    w: Math.max(2, Math.min(100, frame.w)),
    h: Math.max(1, Math.min(100, frame.h)),
  };
}

export function clampFrameForBlock(block: ComunicadoBlock, frame: ComunicadoFrame): ComunicadoFrame {
  if (block.type === "shape") return clampFrameForShapeBlock(block, frame);
  return {
    x: Math.max(0, Math.min(100 - frame.w, frame.x)),
    y: Math.max(0, Math.min(100 - frame.h, frame.y)),
    w: Math.max(2, Math.min(100, frame.w)),
    h: Math.max(1, Math.min(100, frame.h)),
  };
}

/** Frame para seleção / marquee — inclui alvo do ponto sem dimensão. */
export function resolveBlockHitFrame(block: ComunicadoBlock): ComunicadoFrame {
  if (block.type === "shape") {
    return geometryBoundingFrame(resolveShapeGeometry(block));
  }
  return block.frame;
}

export function resolveBlockPlacementStyle(block: ComunicadoBlock): CSSProperties {
  if (block.type !== "shape") {
    return {
      left: `${block.frame.x}%`,
      top: `${block.frame.y}%`,
      width: `${block.frame.w}%`,
      height: `${block.frame.h}%`,
    };
  }

  const geometry = resolveShapeGeometry(block);
  if (geometry.primitive === "point") {
    // Hit-box no DOM (= geometryBoundingFrame) para clique, arraste e outline de seleção.
    // Persistência continua w=h=0 na posição do centro.
    const bbox = geometryBoundingFrame(geometry);
    return {
      left: `${bbox.x}%`,
      top: `${bbox.y}%`,
      width: `${bbox.w}%`,
      height: `${bbox.h}%`,
      overflow: "visible",
    };
  }

  const bbox = geometryBoundingFrame(geometry);
  return {
    left: `${bbox.x}%`,
    top: `${bbox.y}%`,
    width: `${bbox.w}%`,
    height: `${bbox.h}%`,
    ...(geometry.primitive === "line" ? { overflow: "visible" as const } : {}),
  };
}

/** Normaliza vértices de linha após alteração do frame (bbox). */
export function syncLineVerticesFromFrame(
  block: ComunicadoShapeBlock,
  frame: ComunicadoFrame,
): ComunicadoGeometryVertex[] {
  return lineEndpointsFromFrame(frame);
}
