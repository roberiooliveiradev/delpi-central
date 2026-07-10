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
    expect(kinds.length).toBeGreaterThan(8);
  });

  it("valida kind conhecido", () => {
    expect(isComunicadoShapeKind("diamond")).toBe(true);
    expect(isComunicadoShapeKind("unknown-shape")).toBe(false);
  });

  it("fornece rótulo PT para cada kind", () => {
    for (const entry of COMUNICADO_SHAPE_KINDS) {
      expect(comunicadoShapeLabel(entry.kind)).toBe(entry.label);
    }
  });
});
