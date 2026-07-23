import type { CSSProperties } from "react";

import type {
  ComunicadoBlock,
  ComunicadoFrame,
  ComunicadoGeometryVertex,
  ComunicadoShapeBlock,
} from "./comunicadoTypes";
import { clampFramePositionPercent, clampFrameSizePercent } from "./frameDesignPixels";
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

function clampPct(value: number): number {
  return Math.max(0, Math.min(100, value));
}

export function minimumVertexCount(primitive: ComunicadoVisualPrimitive): number {
  if (primitive === "point") return 1;
  if (primitive === "line") return 2;
  return 3;
}

/** Fallback legado: linha horizontal no mid-Y do frame (só quando não há vertices). */
export function lineEndpointsFromFrame(frame: ComunicadoFrame): ComunicadoGeometryVertex[] {
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

/** Endpoints canônicos de uma linha (sempre 2 pontos). */
export function resolveLineEndpoints(
  block: ComunicadoShapeBlock,
): [ComunicadoGeometryVertex, ComunicadoGeometryVertex] {
  const geometry = resolveShapeGeometry(block);
  if (geometry.primitive !== "line") {
    const fallback = lineEndpointsFromFrame(block.frame);
    return [fallback[0]!, fallback[1]!];
  }
  return [
    { x: geometry.points[0]!.x, y: geometry.points[0]!.y },
    {
      x: geometry.points[geometry.points.length - 1]!.x,
      y: geometry.points[geometry.points.length - 1]!.y,
    },
  ];
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
      w: clampFrameSizePercent(rawW) + 2 * pad,
      h: clampFrameSizePercent(rawH) + 2 * pad,
    };
  }

  return {
    x: minX,
    y: minY,
    w: clampFrameSizePercent(rawW),
    h: clampFrameSizePercent(rawH),
  };
}

export function frameFromLineEndpoints(
  a: ComunicadoGeometryVertex,
  b: ComunicadoGeometryVertex,
): ComunicadoFrame {
  return geometryBoundingFrame({ primitive: "line", points: [a, b] });
}

/**
 * Define endpoints da linha (vertices-first) e recalcula o frame.
 * Não força horizontal — diagonais são estáveis.
 */
export function applyLineEndpoints(
  block: ComunicadoShapeBlock,
  a: ComunicadoGeometryVertex,
  b: ComunicadoGeometryVertex,
): ComunicadoShapeBlock {
  const start = { x: clampPct(a.x), y: clampPct(a.y) };
  const end = { x: clampPct(b.x), y: clampPct(b.y) };
  const vertices = [start, end];
  return {
    ...block,
    vertices,
    frame: frameFromLineEndpoints(start, end),
  };
}

/** Translada ambos os endpoints (move do bloco linha). */
export function translateLineEndpoints(
  block: ComunicadoShapeBlock,
  dx: number,
  dy: number,
): ComunicadoShapeBlock {
  const [a, b] = resolveLineEndpoints(block);
  return applyLineEndpoints(
    block,
    { x: a.x + dx, y: a.y + dy },
    { x: b.x + dx, y: b.y + dy },
  );
}

/** Atualiza um único endpoint (0 = início / from, 1 = fim / to). */
export function applyLineEndpointAt(
  block: ComunicadoShapeBlock,
  endpointIndex: 0 | 1,
  point: ComunicadoGeometryVertex,
): ComunicadoShapeBlock {
  const [a, b] = resolveLineEndpoints(block);
  if (endpointIndex === 0) return applyLineEndpoints(block, point, b);
  return applyLineEndpoints(block, a, point);
}

/** Frame persistido: ponto só posição (w=h=0); demais primitivos usam bbox da geometria. */
export function geometryToPersistedFrame(block: ComunicadoShapeBlock): ComunicadoFrame {
  const geometry = resolveShapeGeometry(block);
  if (geometry.primitive === "point") {
    return { x: geometry.position.x, y: geometry.position.y, w: 0, h: 0 };
  }
  return geometryBoundingFrame(geometry);
}

/** Linha e ponto não usam os 8 handles de bbox — linha usa endpoints. */
export function shapeBlockAllowsResize(block: ComunicadoShapeBlock): boolean {
  if (isPointShapeKind(block.shape) || isLineShapeKind(block.shape)) return false;
  return true;
}

export function clampFrameForShapeBlock(block: ComunicadoShapeBlock, frame: ComunicadoFrame): ComunicadoFrame {
  if (isPointShapeKind(block.shape)) {
    return {
      x: clampFramePositionPercent(frame.x),
      y: clampFramePositionPercent(frame.y),
      w: 0,
      h: 0,
    };
  }

  if (isLineShapeKind(block.shape)) {
    return {
      x: clampFramePositionPercent(frame.x),
      y: clampFramePositionPercent(frame.y),
      w: clampFrameSizePercent(frame.w),
      h: clampFrameSizePercent(frame.h),
    };
  }

  return {
    x: clampFramePositionPercent(frame.x),
    y: clampFramePositionPercent(frame.y),
    w: clampFrameSizePercent(frame.w),
    h: clampFrameSizePercent(frame.h),
  };
}

export function clampFrameForBlock(block: ComunicadoBlock, frame: ComunicadoFrame): ComunicadoFrame {
  if (block.type === "shape") return clampFrameForShapeBlock(block, frame);
  return {
    x: clampFramePositionPercent(frame.x),
    y: clampFramePositionPercent(frame.y),
    w: clampFrameSizePercent(frame.w),
    h: clampFrameSizePercent(frame.h),
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

/**
 * @deprecated Preferir `applyLineEndpoints` / `translateLineEndpoints`.
 * Mantido para callers legados: se o frame só transladou (mesmo w/h), preserva diagonal;
 * caso contrário (resize de bbox), regenera horizontal no mid-Y.
 */
export function syncLineVerticesFromFrame(
  block: ComunicadoShapeBlock,
  frame: ComunicadoFrame,
): ComunicadoGeometryVertex[] {
  const [a, b] = resolveLineEndpoints(block);
  const sameSize =
    Math.abs(frame.w - block.frame.w) < 0.01 && Math.abs(frame.h - block.frame.h) < 0.01;
  if (sameSize) {
    const dx = frame.x - block.frame.x;
    const dy = frame.y - block.frame.y;
    return [
      { x: clampPct(a.x + dx), y: clampPct(a.y + dy) },
      { x: clampPct(b.x + dx), y: clampPct(b.y + dy) },
    ];
  }
  return lineEndpointsFromFrame(frame);
}

/** Vertices iniciais para um bloco linha a partir do frame default. */
export function initialLineVerticesFromFrame(frame: ComunicadoFrame): ComunicadoGeometryVertex[] {
  return lineEndpointsFromFrame(frame);
}
