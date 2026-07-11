import { describe, expect, it } from "vitest";

import {
  COMUNICADO_SHAPE_CATALOG_CATEGORIES,
  COMUNICADO_SHAPE_KIND_VALUES,
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
