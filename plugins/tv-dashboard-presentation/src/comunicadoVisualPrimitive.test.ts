import { describe, expect, it } from "vitest";

import {
  defaultStrokeWidthForPrimitive,
  isAreaShapeKind,
  isLineShapeKind,
  isPointShapeKind,
  resolveShapePrimitive,
  shapeSupportsFill,
  shapeSupportsStroke,
} from "./comunicadoVisualPrimitive";

describe("comunicadoVisualPrimitive", () => {
  it("classifica ponto, linha e área", () => {
    expect(resolveShapePrimitive("point")).toBe("point");
    expect(resolveShapePrimitive("line")).toBe("line");
    expect(resolveShapePrimitive("line-arrow-right")).toBe("line");
    expect(resolveShapePrimitive("rectangle")).toBe("area");
    expect(resolveShapePrimitive("ellipse")).toBe("area");
    expect(resolveShapePrimitive("flowchart-decision")).toBe("area");
  });

  it("expõe helpers por primitivo", () => {
    expect(isPointShapeKind("point")).toBe(true);
    expect(isPointShapeKind("line")).toBe(false);
    expect(isLineShapeKind("line-arrow-right")).toBe(true);
    expect(isLineShapeKind("point")).toBe(false);
    expect(isAreaShapeKind("diamond")).toBe(true);
    expect(isAreaShapeKind("line")).toBe(false);
  });

  it("define espessura padrão por primitivo", () => {
    expect(defaultStrokeWidthForPrimitive("point")).toBe(0);
    expect(defaultStrokeWidthForPrimitive("line")).toBe(4);
    expect(defaultStrokeWidthForPrimitive("area")).toBe(2);
  });

  it("indica suporte a preenchimento e contorno", () => {
    expect(shapeSupportsFill("point")).toBe(true);
    expect(shapeSupportsFill("line")).toBe(false);
    expect(shapeSupportsFill("area")).toBe(true);

    expect(shapeSupportsStroke("point")).toBe(false);
    expect(shapeSupportsStroke("line")).toBe(true);
    expect(shapeSupportsStroke("area")).toBe(true);
  });
});
