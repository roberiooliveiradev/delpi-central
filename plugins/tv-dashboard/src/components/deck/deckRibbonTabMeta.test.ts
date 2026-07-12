import { describe, expect, it } from "vitest";

import {
  resolveDeckRibbonTabs,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deckRibbonTabMeta";

describe("deckRibbonTabMeta (Onda 4K/4L)", () => {
  it("mostra aba Forma para KPI/tabela/gráfico (chrome de forma)", () => {
    const tabs = resolveDeckRibbonTabs(true, { shapeChromeSelected: true });
    expect(tabs.some((tab) => tab.id === "shape")).toBe(true);
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

  it("sempre inclui Programação e Página Inicial", () => {
    const tabs = resolveDeckRibbonTabs(true);
    expect(tabs.map((tab) => tab.id)).toEqual(
      expect.arrayContaining(["home", "playlist", "slide", "insert"]),
    );
    expect(tabs.find((tab) => tab.id === "playlist")?.label).toBe("Programação");
  });
});
