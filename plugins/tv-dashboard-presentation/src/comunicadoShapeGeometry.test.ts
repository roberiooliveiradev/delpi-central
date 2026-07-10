import { describe, expect, it } from "vitest";

import { createShapeBlock } from "./comunicadoHelpers";
import {
  COMUNICADO_POINT_HIT_SIZE_PCT,
  geometryBoundingFrame,
  geometryToPersistedFrame,
  minimumVertexCount,
  resolveShapeGeometry,
  shapeBlockAllowsResize,
} from "./comunicadoShapeGeometry";

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

  it("linha é formada por pelo menos dois pontos", () => {
    const block = createShapeBlock("line");
    const geometry = resolveShapeGeometry(block);
    expect(geometry.primitive).toBe("line");
    if (geometry.primitive !== "line") return;
    expect(geometry.points.length).toBeGreaterThanOrEqual(2);
    expect(geometry.points[0].y).toBe(geometry.points[1].y);
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
