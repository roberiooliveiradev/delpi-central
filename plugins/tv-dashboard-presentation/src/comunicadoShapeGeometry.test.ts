import { describe, expect, it } from "vitest";

import { createShapeBlock } from "./comunicadoHelpers";
import {
  COMUNICADO_LINE_VISUAL_PAD_PCT,
  COMUNICADO_POINT_HIT_SIZE_PCT,
  applyLineEndpoints,
  geometryBoundingFrame,
  geometryToPersistedFrame,
  minimumVertexCount,
  resolveBlockPlacementStyle,
  resolveLineEndpoints,
  resolveShapeGeometry,
  shapeBlockAllowsResize,
  translateLineEndpoints,
} from "./comunicadoShapeGeometry";
import { lineArrowHeadPolygonPoints } from "./comunicadoShapeGraphic";

describe("comunicadoShapeGeometry", () => {
  it("exige contagem mínima de vértices por primitivo", () => {
    expect(minimumVertexCount("point")).toBe(1);
    expect(minimumVertexCount("line")).toBe(2);
    expect(minimumVertexCount("area")).toBe(3);
  });

  it("ponto não tem dimensão — só posição", () => {
    const block = createShapeBlock("point");
    const geometry = resolveShapeGeometry(block);
    expect(geometry.primitive).toBe("point");
    if (geometry.primitive !== "point") return;
    expect(geometry.position).toEqual({ x: 45, y: 45 });
    expect(geometryToPersistedFrame(block)).toEqual({ x: 45, y: 45, w: 0, h: 0 });
    expect(shapeBlockAllowsResize(block)).toBe(false);
  });

  it("linha é formada por pelo menos dois pontos (vertices iniciais)", () => {
    const block = createShapeBlock("line");
    expect(block.type).toBe("shape");
    if (block.type !== "shape") return;
    expect(block.vertices?.length).toBeGreaterThanOrEqual(2);
    const geometry = resolveShapeGeometry(block);
    expect(geometry.primitive).toBe("line");
    if (geometry.primitive !== "line") return;
    expect(geometry.points.length).toBeGreaterThanOrEqual(2);
    expect(geometry.points[0].y).toBe(geometry.points[1].y);
    expect(shapeBlockAllowsResize(block)).toBe(false);
  });

  it("applyLineEndpoints preserva diagonal e recalcula frame", () => {
    const block = createShapeBlock("line");
    if (block.type !== "shape") return;
    const next = applyLineEndpoints(block, { x: 10, y: 10 }, { x: 80, y: 70 });
    const [a, b] = resolveLineEndpoints(next);
    expect(a).toEqual({ x: 10, y: 10 });
    expect(b).toEqual({ x: 80, y: 70 });
    expect(next.frame.w).toBeGreaterThan(next.frame.h);
    const moved = translateLineEndpoints(next, 5, -5);
    const [ma, mb] = resolveLineEndpoints(moved);
    expect(ma).toEqual({ x: 15, y: 5 });
    expect(mb).toEqual({ x: 85, y: 65 });
  });

  it("bbox de linha horizontal inclui padding para seta/espessura", () => {
    const block = createShapeBlock("line-arrow-right");
    const geometry = resolveShapeGeometry(block);
    if (geometry.primitive !== "line") return;
    const bbox = geometryBoundingFrame(geometry);
    expect(bbox.h).toBeGreaterThanOrEqual(2 * COMUNICADO_LINE_VISUAL_PAD_PCT);
    expect(bbox.w).toBeGreaterThan(bbox.h);
    expect(geometryToPersistedFrame(block).h).toBe(bbox.h);
  });

  it("forma fechada usa polígono com pelo menos três vértices", () => {
    const block = createShapeBlock("rectangle");
    const geometry = resolveShapeGeometry(block);
    expect(geometry.primitive).toBe("area");
    if (geometry.primitive !== "area") return;
    expect(geometry.points.length).toBeGreaterThanOrEqual(3);
    expect(geometry.points[0]).toEqual({ x: 30, y: 30 });
    expect(geometry.points[2]).toEqual({ x: 70, y: 70 });
  });

  it("bbox do ponto usa apenas alvo de seleção", () => {
    const block = createShapeBlock("point");
    const geometry = resolveShapeGeometry(block);
    if (geometry.primitive !== "point") return;
    const bbox = geometryBoundingFrame(geometry);
    expect(bbox.w).toBe(COMUNICADO_POINT_HIT_SIZE_PCT);
    expect(bbox.h).toBe(COMUNICADO_POINT_HIT_SIZE_PCT);
  });

  it("placement do ponto usa hit-box (não 0×0) para clique/seleção", () => {
    const block = createShapeBlock("point");
    const style = resolveBlockPlacementStyle(block);
    expect(style.width).toBe(`${COMUNICADO_POINT_HIT_SIZE_PCT}%`);
    expect(style.height).toBe(`${COMUNICADO_POINT_HIT_SIZE_PCT}%`);
    expect(style.transform).toBeUndefined();
  });

  it("migra frame legado com dimensão para posição central do ponto", () => {
    const block = {
      ...createShapeBlock("point"),
      frame: { x: 40, y: 40, w: 10, h: 10 },
    };
    const geometry = resolveShapeGeometry(block);
    if (geometry.primitive !== "point") return;
    expect(geometry.position).toEqual({ x: 45, y: 45 });
  });
});

describe("lineArrowHeadPolygonPoints", () => {
  it("seta horizontal tem abertura vertical visível após compensar aspect achatado", () => {
    const boxAspect = (84 / 4) * (16 / 9);
    const points = lineArrowHeadPolygonPoints({ x: 96, y: 50 }, { x: 4, y: 50 }, boxAspect);
    const coords = points.split(/\s+/).map((pair) => {
      const [x, y] = pair.split(",").map(Number);
      return { x, y };
    });
    expect(coords).toHaveLength(3);
    const ys = coords.map((c) => c.y);
    const spanY = Math.max(...ys) - Math.min(...ys);
    expect(spanY).toBeGreaterThan(30);
    expect(Math.min(...ys)).toBeGreaterThanOrEqual(0);
    expect(Math.max(...ys)).toBeLessThanOrEqual(100);
  });
});
