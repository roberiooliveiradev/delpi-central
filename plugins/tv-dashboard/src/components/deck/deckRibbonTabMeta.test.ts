import { describe, expect, it } from "vitest";

import {
  resolveDeckRibbonTabs,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deckRibbonTabMeta";

describe("deckRibbonTabMeta (Onda 4K)", () => {
  it("mostra aba Forma só com shape selecionada", () => {
    const without = resolveDeckRibbonTabs(true, { shapeSelected: false });
    const withShape = resolveDeckRibbonTabs(true, { shapeSelected: true });
    expect(without.some((tab) => tab.id === "shape")).toBe(false);
    expect(withShape.some((tab) => tab.id === "shape")).toBe(true);
  });

  it("mantém Gráfico e Forma independentes no chrome embutido", () => {
    const both = resolveEmbeddedComunicadoRibbonTabs({
      chartSelected: true,
      shapeSelected: true,
    });
    expect(both.map((tab) => tab.id)).toEqual(
      expect.arrayContaining(["insert", "format", "chart", "shape", "view"]),
    );
  });
});
