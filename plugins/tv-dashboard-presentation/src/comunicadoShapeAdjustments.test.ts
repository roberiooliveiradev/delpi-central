import { describe, expect, it } from "vitest";

import {
  defaultShapeAdjustments,
  patchShapeAdjustment,
  resolveShapeAdjustments,
  shapeAdjustmentSpecs,
  shapeHasAdjustments,
} from "./comunicadoShapeAdjustments";
import { COMUNICADO_SHAPE_KIND_VALUES } from "./comunicadoShapeCatalog";
import {
  arrowRightPath,
  hexagonPoints,
  parallelogramPoints,
  trapezoidPoints,
  trianglePoints,
} from "./comunicadoShapePaths";

describe("comunicadoShapeAdjustments", () => {
  it("expõe ajustes para formas do catálogo com geometria editável", () => {
    expect(shapeHasAdjustments("rectangle")).toBe(false);
    expect(shapeHasAdjustments("ellipse")).toBe(false);
    expect(shapeHasAdjustments("rounded-rect")).toBe(true);
    expect(shapeHasAdjustments("hexagon")).toBe(true);
    expect(shapeHasAdjustments("arrow-right")).toBe(true);
    expect(shapeHasAdjustments("diamond")).toBe(false);
    expect(shapeHasAdjustments("point")).toBe(false);
  });

  it("resolve defaults e legado borderRadius → adj de cantos (rounded-rect)", () => {
    expect(defaultShapeAdjustments("rectangle")).toEqual([]);
    expect(defaultShapeAdjustments("rounded-rect")[0]).toBeCloseTo(0.16);
    const fromLegacy = resolveShapeAdjustments("rounded-rect", { borderRadius: 16 });
    expect(fromLegacy[0]).toBeCloseTo(0.25);
    expect(resolveShapeAdjustments("rounded-rect", { borderRadius: 0 })[0]).toBe(0);
    expect(resolveShapeAdjustments("rounded-rect", {})[0]).toBeCloseTo(0.16);
  });

  it("patchShapeAdjustment atualiza adjustments e borderRadius nos cantos", () => {
    const patch = patchShapeAdjustment("rounded-rect", {}, 0, 0.25, 80);
    expect(patch.adjustments?.[0]).toBeCloseTo(0.25);
    expect(patch.borderRadius).toBe(20);
  });

  it("cada spec tem handleAt e valueFromPointer coerentes", () => {
    for (const kind of COMUNICADO_SHAPE_KIND_VALUES) {
      const specs = shapeAdjustmentSpecs(kind);
      const values = defaultShapeAdjustments(kind);
      for (const spec of specs) {
        const pos = spec.handleAt(values);
        expect(pos.x).toBeGreaterThanOrEqual(0);
        expect(pos.x).toBeLessThanOrEqual(100);
        expect(pos.y).toBeGreaterThanOrEqual(0);
        expect(pos.y).toBeLessThanOrEqual(110);
        const next = spec.valueFromPointer(pos.x, pos.y, values);
        expect(next).toBeGreaterThanOrEqual(spec.min);
        expect(next).toBeLessThanOrEqual(spec.max);
      }
    }
  });

  it("handle laranja de cantos: posição e ponteiro são inversos (distância estável)", () => {
    const spec = shapeAdjustmentSpecs("rounded-rect")[0]!;
    for (const adj of [0, 0.1, 0.16, 0.25, 0.5]) {
      const pos = spec.handleAt([adj]);
      expect(pos.x).toBeGreaterThanOrEqual(12);
      expect(pos.x).toBeLessThanOrEqual(50);
      expect(spec.valueFromPointer(pos.x, pos.y, [adj])).toBeCloseTo(adj, 5);
    }
    // Raio 0 não cobre o handle NW (0%,0%).
    expect(spec.handleAt([0]).x).toBeGreaterThan(8);
  });

  it("paths parametrizados respondem ao ajuste", () => {
    const flat = parallelogramPoints([0.1]);
    const steep = parallelogramPoints([0.4]);
    expect(flat[0]).not.toBe(steep[0]);
    expect(trianglePoints([0.2])[0]).toBeCloseTo(20);
    expect(trianglePoints([0.8])[0]).toBeCloseTo(80);
  });

  it("gesto de adjust: default → drag → path muda (trapézio, hexágono, seta)", () => {
    const cases: Array<{
      kind: "trapezoid" | "hexagon" | "arrow-right";
      dragTo: { x: number; y: number };
      pathBefore: (values: number[]) => string | number[];
    }> = [
      {
        kind: "trapezoid",
        dragTo: { x: 40, y: 12 },
        pathBefore: (v) => trapezoidPoints(v),
      },
      {
        kind: "hexagon",
        dragTo: { x: 85, y: 50 },
        pathBefore: (v) => hexagonPoints(v),
      },
      {
        kind: "arrow-right",
        dragTo: { x: 50, y: 20 },
        pathBefore: (v) => arrowRightPath(v),
      },
    ];
    for (const item of cases) {
      const spec = shapeAdjustmentSpecs(item.kind)[0]!;
      const before = defaultShapeAdjustments(item.kind);
      const after = [...before];
      after[spec.index] = spec.valueFromPointer(item.dragTo.x, item.dragTo.y, before);
      expect(after[spec.index]).not.toBeCloseTo(before[spec.index]!, 3);
      expect(JSON.stringify(item.pathBefore(after))).not.toBe(JSON.stringify(item.pathBefore(before)));
      const handle = spec.handleAt(after);
      expect(spec.valueFromPointer(handle.x, handle.y, after)).toBeCloseTo(after[spec.index]!, 2);
    }
  });
});
