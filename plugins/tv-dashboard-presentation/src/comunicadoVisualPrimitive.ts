import type { ComunicadoShapeKind } from "./comunicadoTypes";

/**
 * Hierarquia geométrica: ponto (0D) → linha (≥2 pontos) → forma fechada por arestas (≥3 vértices).
 * Geometria canônica em `comunicadoShapeGeometry.ts`.
 */
export type ComunicadoVisualPrimitive = "point" | "line" | "area";

const POINT_SHAPE_KINDS = new Set<ComunicadoShapeKind>(["point"]);
const LINE_SHAPE_KINDS = new Set<ComunicadoShapeKind>(["line", "line-arrow-right"]);

export function resolveShapePrimitive(kind: ComunicadoShapeKind): ComunicadoVisualPrimitive {
  if (POINT_SHAPE_KINDS.has(kind)) return "point";
  if (LINE_SHAPE_KINDS.has(kind)) return "line";
  return "area";
}

export function isPointShapeKind(kind: ComunicadoShapeKind): boolean {
  return resolveShapePrimitive(kind) === "point";
}

export function isLineShapeKind(kind: ComunicadoShapeKind): boolean {
  return resolveShapePrimitive(kind) === "line";
}

export function isAreaShapeKind(kind: ComunicadoShapeKind): boolean {
  return resolveShapePrimitive(kind) === "area";
}

export function defaultStrokeWidthForPrimitive(primitive: ComunicadoVisualPrimitive): number {
  if (primitive === "point") return 0;
  if (primitive === "line") return 4;
  return 2;
}

/** Linhas não têm preenchimento; ponto e área sim (ponto usa fill como cor do marcador). */
export function shapeSupportsFill(primitive: ComunicadoVisualPrimitive): boolean {
  return primitive !== "line";
}

/** Linha e área sempre; ponto aceita contorno opcional do marcador. */
export function shapeSupportsStroke(primitive: ComunicadoVisualPrimitive): boolean {
  return primitive === "line" || primitive === "area" || primitive === "point";
}
