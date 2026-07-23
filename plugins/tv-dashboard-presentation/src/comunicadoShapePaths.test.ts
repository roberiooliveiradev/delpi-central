import { describe, expect, it } from "vitest";

import {
  arrowDownPath,
  arrowLeftPath,
  arrowLeftRightPath,
  arrowRightPath,
  arrowUpDownPath,
  arrowUpPath,
  bentArrowPath,
  calloutCloudPath,
  chevronLeftPath,
  chevronRightPath,
  lightningPath,
  notchedArrowPath,
  piePath,
  regularPolygonPoints,
  smileyMouthPath,
  teardropPath,
} from "./comunicadoShapePaths";
import { COMUNICADO_SHAPE_KIND_VALUES, isComunicadoShapeKind } from "./comunicadoShapeCatalog";
import { createShapeBlock } from "./comunicadoHelpers";
import { resolveShapePrimitive } from "./comunicadoVisualPrimitive";

function pathNumbers(d: string): number[] {
  return (d.match(/-?\d+(\.\d+)?/g) ?? []).map(Number);
}

describe("comunicadoShapePaths — setas Office-like", () => {
  it("arrow-right tem ponta limpa em (96,50) e só dois L (sem barbas)", () => {
    const d = arrowRightPath([0.35, 0.28]);
    expect(d).toContain("L96 50");
    expect(d).toContain("V8");
    expect(d).toMatch(/L\d+(\.\d+)? 92/);
    const lineTos = d.match(/L/g) ?? [];
    expect(lineTos).toHaveLength(2);
  });

  it("ajuste de cabeça/corpo altera o path (default → drag)", () => {
    const slim = arrowRightPath([0.2, 0.15]);
    const wide = arrowRightPath([0.5, 0.4]);
    expect(slim).not.toBe(wide);
    expect(arrowLeftPath([0.35, 0.28])).toContain("L4 50");
    expect(arrowUpPath([0.35, 0.28])).toContain("L50 4");
    expect(arrowDownPath([0.35, 0.28])).toContain("L50 96");
    expect(arrowLeftRightPath([0.35, 0.28])).toContain("L96 50");
    expect(arrowLeftRightPath([0.35, 0.28])).toContain("L4 50");
    expect(arrowUpDownPath([0.35, 0.28])).toContain("L50 4");
    expect(arrowUpDownPath([0.35, 0.28])).toContain("L50 96");
  });

  it("chevron é sólido estilo PowerPoint (não faixa oca em V)", () => {
    const right = chevronRightPath([0.45]);
    const left = chevronLeftPath([0.45]);
    expect(right).toContain("L96 50");
    expect(left).toContain("L4 50");
    expect((right.match(/L/g) ?? []).length).toBeGreaterThanOrEqual(2);
    expect((left.match(/L/g) ?? []).length).toBeGreaterThanOrEqual(2);
    expect(chevronRightPath([0.2])).not.toBe(chevronRightPath([0.7]));
  });

  it("notched-arrow tem entalhe na base e ponta limpa", () => {
    const d = notchedArrowPath([0.35, 0.28]);
    expect(d).toContain("L96 50");
    expect(d).toMatch(/L\d+(\.\d+)? 50 Z$/);
    expect(notchedArrowPath([0.2, 0.2])).not.toBe(notchedArrowPath([0.5, 0.4]));
  });

  it("novas formas da Fase 1 geram geometria válida", () => {
    expect(regularPolygonPoints(7)).toHaveLength(14);
    expect(regularPolygonPoints(12)).toHaveLength(24);
    expect(bentArrowPath([0.28, 0.22])).toContain("Z");
    expect(teardropPath().startsWith("M")).toBe(true);
    expect(COMUNICADO_SHAPE_KIND_VALUES.length).toBeGreaterThan(80);
    for (const kind of ["heptagon", "donut", "bent-arrow", "star-16", "callout-oval"] as const) {
      expect(isComunicadoShapeKind(kind)).toBe(true);
      const block = createShapeBlock(kind);
      expect(block.type).toBe("shape");
      if (block.type === "shape") {
        expect(resolveShapePrimitive(block.shape)).toBe("area");
      }
    }
  });

  it("raio, pizza, carinha e balão-nuvem têm path contínuo e responsivo ao ajuste", () => {
    expect(lightningPath([0.2])).not.toBe(lightningPath([0.8]));
    expect(piePath([0.3])).not.toBe(piePath([0.85]));
    expect(smileyMouthPath([0.2])).not.toBe(smileyMouthPath([0.9]));
    const cloud = calloutCloudPath([0.5, 0.9]);
    expect(cloud).toContain("Z");
    expect(cloud.match(/L/g)?.length ?? 0).toBeGreaterThanOrEqual(3);
  });
});
