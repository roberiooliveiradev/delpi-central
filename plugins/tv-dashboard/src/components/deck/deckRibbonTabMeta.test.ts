import { describe, expect, it } from "vitest";

import {
  resolveDeckRibbonTabs,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deckRibbonTabMeta";

describe("deckRibbonTabMeta (Onda 4K/4L)", () => {
  it("mostra aba Forma só com shape selecionada", () => {
    const without = resolveDeckRibbonTabs(true, { shapeSelected: false });
    const withShape = resolveDeckRibbonTabs(true, { shapeSelected: true });
    expect(without.some((tab) => tab.id === "shape")).toBe(false);
    expect(withShape.some((tab) => tab.id === "shape")).toBe(true);
  });

  it("mostra aba Forma com parte geométrica de gráfico", () => {
    const tabs = resolveDeckRibbonTabs(true, {
      chartSelected: true,
      chartPartPrimitiveSelected: true,
    });
    expect(tabs.some((tab) => tab.id === "shape")).toBe(true);
    expect(tabs.some((tab) => tab.id === "chart")).toBe(true);
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
