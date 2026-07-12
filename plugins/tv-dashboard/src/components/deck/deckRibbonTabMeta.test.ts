import { describe, expect, it } from "vitest";

import {
  isContextualDeckRibbonTab,
  resolveDeckRibbonTabs,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deckRibbonTabMeta";

describe("deckRibbonTabMeta (contextuais sem Formatar)", () => {
  it("mostra aba Forma para KPI/tabela/gráfico (chrome de forma)", () => {
    const tabs = resolveDeckRibbonTabs(true, { shapeChromeSelected: true });
    expect(tabs.some((tab) => tab.id === "shape")).toBe(true);
  });

  it("mostra aba Forma para caixa de texto / mídia", () => {
    const tabs = resolveDeckRibbonTabs(true, { textOrMediaSelected: true });
    expect(tabs.some((tab) => tab.id === "shape")).toBe(true);
    expect(tabs.some((tab) => tab.id === "format")).toBe(false);
  });

  it("mostra aba Tabela e Forma com table_view selecionado", () => {
    const tabs = resolveDeckRibbonTabs(true, {
      tableSelected: true,
      shapeChromeSelected: true,
      dataSelected: true,
    });
    expect(tabs.some((tab) => tab.id === "table")).toBe(true);
    expect(tabs.some((tab) => tab.id === "shape")).toBe(true);
    expect(tabs.some((tab) => tab.id === "data")).toBe(true);
    expect(tabs.find((tab) => tab.id === "table")?.label).toBe("Tabela");
  });

  it("coloca abas contextuais depois das permanentes, Dados no fim", () => {
    const tabs = resolveDeckRibbonTabs(true, {
      chartSelected: true,
      tableSelected: true,
      shapeChromeSelected: true,
      dataSelected: true,
    });
    const ids = tabs.map((tab) => tab.id);
    const playlistIdx = ids.indexOf("playlist");
    const chartIdx = ids.indexOf("chart");
    const dataIdx = ids.indexOf("data");
    expect(playlistIdx).toBeGreaterThan(-1);
    expect(chartIdx).toBeGreaterThan(playlistIdx);
    expect(dataIdx).toBe(ids.length - 1);
    expect(isContextualDeckRibbonTab(tabs[dataIdx]!)).toBe(true);
    expect(isContextualDeckRibbonTab(tabs.find((t) => t.id === "home")!)).toBe(false);
  });

  it("mostra aba Forma com parte geométrica de gráfico", () => {
    const tabs = resolveDeckRibbonTabs(true, {
      chartSelected: true,
      chartPartPrimitiveSelected: true,
    });
    expect(tabs.some((tab) => tab.id === "shape")).toBe(true);
    expect(tabs.some((tab) => tab.id === "chart")).toBe(true);
  });

  it("mantém contextuais no final do chrome embutido sem Formatar", () => {
    const both = resolveEmbeddedComunicadoRibbonTabs({
      chartSelected: true,
      tableSelected: true,
      shapeSelected: true,
      dataSelected: true,
    });
    expect(both.map((tab) => tab.id)).toEqual([
      "insert",
      "view",
      "chart",
      "table",
      "shape",
      "data",
    ]);
  });

  it("sempre inclui Programação e Página Inicial e nunca Formatar", () => {
    const tabs = resolveDeckRibbonTabs(true);
    expect(tabs.map((tab) => tab.id)).toEqual(
      expect.arrayContaining(["home", "playlist", "slide", "insert"]),
    );
    expect(tabs.find((tab) => tab.id === "playlist")?.label).toBe("Programação");
    expect(tabs.some((tab) => tab.id === "data")).toBe(false);
    expect(tabs.some((tab) => tab.id === "format")).toBe(false);
  });
});
