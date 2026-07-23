import { describe, expect, it } from "vitest";

import {
  COMUNICADO_LINE_TOOLS,
  COMUNICADO_SHAPE_CATALOG_CATEGORIES,
  COMUNICADO_SHAPE_KIND_VALUES,
  COMUNICADO_SHAPE_LIBRARY_FLYOUT_CATEGORIES,
  isComunicadoShapeKind,
} from "./comunicadoShapeCatalog";
import { createShapeBlock } from "./comunicadoHelpers";
import { resolveShapePrimitive } from "./comunicadoVisualPrimitive";

describe("comunicadoShapeCatalog (Onda 4K)", () => {
  it("expõe labels para todos os kinds do union", () => {
    expect(COMUNICADO_SHAPE_KIND_VALUES.length).toBeGreaterThan(30);
    for (const kind of COMUNICADO_SHAPE_KIND_VALUES) {
      expect(isComunicadoShapeKind(kind)).toBe(true);
    }
  });

  it("categorias cobrem exatamente o conjunto de kinds", () => {
    const fromCategories = COMUNICADO_SHAPE_CATALOG_CATEGORIES.flatMap((category) => category.shapes);
    expect(new Set(fromCategories).size).toBe(fromCategories.length);
    expect(new Set(fromCategories)).toEqual(new Set(COMUNICADO_SHAPE_KIND_VALUES));
  });

  it("flyout Formas segue categorias Google Slides (sem linhas)", () => {
    expect(COMUNICADO_SHAPE_LIBRARY_FLYOUT_CATEGORIES.map((c) => c.id)).toEqual([
      "formas",
      "setas",
      "descricoes",
      "equacao",
    ]);
    const flyoutKinds = COMUNICADO_SHAPE_LIBRARY_FLYOUT_CATEGORIES.flatMap((c) => c.shapes);
    expect(flyoutKinds.some((kind) => resolveShapePrimitive(kind) === "line")).toBe(false);
  });

  it("menu Linha lista as 7 ferramentas do Google Slides", () => {
    expect(COMUNICADO_LINE_TOOLS.map((tool) => tool.id)).toEqual([
      "line",
      "line-arrow",
      "elbow-connector",
      "curved-connector",
      "curve",
      "polyline",
      "scribble",
    ]);
    expect(COMUNICADO_LINE_TOOLS.filter((tool) => tool.ready).map((tool) => tool.id)).toEqual([
      "line",
      "line-arrow",
      "elbow-connector",
      "curved-connector",
      "curve",
      "polyline",
      "scribble",
    ]);
  });

  it("cria bloco shape com primitivo coerente para linha e área", () => {
    const line = createShapeBlock("line-arrow-both");
    const area = createShapeBlock("flowchart-decision");
    expect(line.type).toBe("shape");
    expect(area.type).toBe("shape");
    if (line.type === "shape") {
      expect(resolveShapePrimitive(line.shape)).toBe("line");
    }
    if (area.type === "shape") {
      expect(resolveShapePrimitive(area.shape)).toBe("area");
    }
  });
});
