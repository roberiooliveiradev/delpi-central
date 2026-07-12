import { describe, expect, it } from "vitest";

import {
  resolveDeckRibbonTabs,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deckRibbonTabMeta";

describe("deckRibbonTabMeta (Onda 4K/4L/Tabela)", () => {
  it("mostra aba Forma para KPI/tabela/gráfico (chrome de forma)", () => {
    const tabs = resolveDeckRibbonTabs(true, { shapeChromeSelected: true });
    expect(tabs.some((tab) => tab.id === "shape")).toBe(true);
  });

  it("mostra aba Tabela e Forma com table_view selecionado", () => {
    const tabs = resolveDeckRibbonTabs(true, {
      tableSelected: true,
      shapeChromeSelected: true,
    });
    expect(tabs.some((tab) => tab.id === "table")).toBe(true);
    expect(tabs.some((tab) => tab.id === "shape")).toBe(true);
    expect(tabs.find((tab) => tab.id === "table")?.label).toBe("Tabela");
  });

  it("mostra aba Forma com parte geométrica de gráfico", () => {
    const tabs = resolveDeckRibbonTabs(true, {
      chartSelected: true,
      chartPartPrimitiveSelected: true,
    });
    expect(tabs.some((tab) => tab.id === "shape")).toBe(true);
    expect(tabs.some((tab) => tab.id === "chart")).toBe(true);
  });

  it("mantém Gráfico, Tabela e Forma independentes no chrome embutido", () => {
    const both = resolveEmbeddedComunicadoRibbonTabs({
      chartSelected: true,
      tableSelected: true,
      shapeSelected: true,
    });
    expect(both.map((tab) => tab.id)).toEqual(
      expect.arrayContaining(["insert", "format", "chart", "table", "shape", "view"]),
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
