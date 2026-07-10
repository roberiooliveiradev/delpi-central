import { describe, expect, it } from "vitest";

import {
  COMUNICADO_SHAPE_CATALOG_CATEGORIES,
  COMUNICADO_SHAPE_KINDS,
  comunicadoShapeLabel,
  isComunicadoShapeKind,
} from "../src/comunicadoShapeCatalog";

describe("comunicadoShapeCatalog", () => {
  it("expõe categorias com formas únicas", () => {
    const kinds = COMUNICADO_SHAPE_CATALOG_CATEGORIES.flatMap((category) => category.shapes);
    expect(new Set(kinds).size).toBe(kinds.length);
    expect(kinds.length).toBe(23);
  });

  it("ordena categorias na hierarquia ponto → linha → formas", () => {
    expect(COMUNICADO_SHAPE_CATALOG_CATEGORIES[0]?.id).toBe("points");
    expect(COMUNICADO_SHAPE_CATALOG_CATEGORIES[0]?.label).toBe("Pontos");
    expect(COMUNICADO_SHAPE_CATALOG_CATEGORIES[0]?.shapes).toEqual(["point"]);
    expect(COMUNICADO_SHAPE_CATALOG_CATEGORIES[1]?.id).toBe("lines");
    expect(COMUNICADO_SHAPE_CATALOG_CATEGORIES[1]?.primitive).toBe("line");
    expect(COMUNICADO_SHAPE_CATALOG_CATEGORIES[2]?.id).toBe("rectangles");
    expect(COMUNICADO_SHAPE_CATALOG_CATEGORIES[2]?.primitive).toBe("area");
  });

  it("valida kind conhecido", () => {
    expect(isComunicadoShapeKind("point")).toBe(true);
    expect(isComunicadoShapeKind("diamond")).toBe(true);
    expect(isComunicadoShapeKind("unknown-shape")).toBe(false);
  });

  it("fornece rótulo PT para cada kind", () => {
    for (const entry of COMUNICADO_SHAPE_KINDS) {
      expect(comunicadoShapeLabel(entry.kind)).toBe(entry.label);
    }
  });
});
