import { describe, expect, it } from "vitest";

import {
  isContextualDeckRibbonTab,
  resolveDeckRibbonTabs,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deckRibbonTabMeta";

describe("deckRibbonTabMeta (Elemento / Tabela / Dados / Camadas)", () => {
  it("mostra abas Elemento, Dados e Camadas com seleção não-tabela", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: true, isTableSelection: false });
    expect(tabs.map((tab) => tab.id)).toEqual(
      expect.arrayContaining(["element", "data", "layers"]),
    );
    expect(tabs.some((tab) => tab.id === "tableDesign")).toBe(false);
    expect(tabs.find((tab) => tab.id === "element")?.label).toBe("Elemento");
  });

  it("com tabela selecionada troca Elemento por Design + Layout", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: true, isTableSelection: true });
    const ids = tabs.map((tab) => tab.id);
    expect(ids).toEqual(expect.arrayContaining(["tableDesign", "tableLayout", "data", "layers"]));
    expect(ids).not.toContain("element");
    expect(tabs.find((tab) => tab.id === "tableDesign")?.label).toBe("Design da Tabela");
    expect(tabs.find((tab) => tab.id === "tableLayout")?.label).toBe("Tabela Layout");
  });

  it("esconde contextuais sem seleção", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: false });
    expect(tabs.some((tab) => tab.selectionOnly)).toBe(false);
  });

  it("coloca contextuais depois das permanentes", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: true });
    const ids = tabs.map((tab) => tab.id);
    const playlistIdx = ids.indexOf("playlist");
    const elementIdx = ids.indexOf("element");
    const layersIdx = ids.indexOf("layers");
    expect(playlistIdx).toBeGreaterThan(-1);
    expect(elementIdx).toBeGreaterThan(playlistIdx);
    expect(layersIdx).toBe(ids.length - 1);
    expect(isContextualDeckRibbonTab(tabs[layersIdx]!)).toBe(true);
    expect(isContextualDeckRibbonTab(tabs.find((t) => t.id === "home")!)).toBe(false);
  });

  it("chrome embutido inclui Inserir, Exibir e as contextuais", () => {
    const both = resolveEmbeddedComunicadoRibbonTabs({ hasSelection: true });
    expect(both.map((tab) => tab.id)).toEqual([
      "insert",
      "view",
      "element",
      "data",
      "layers",
    ]);
  });

  it("chrome embutido com tabela usa Design/Layout", () => {
    const both = resolveEmbeddedComunicadoRibbonTabs({
      hasSelection: true,
      isTableSelection: true,
    });
    expect(both.map((tab) => tab.id)).toEqual([
      "insert",
      "view",
      "tableDesign",
      "tableLayout",
      "data",
      "layers",
    ]);
  });

  it("sempre inclui Programação e Página Inicial", () => {
    const tabs = resolveDeckRibbonTabs(true);
    expect(tabs.map((tab) => tab.id)).toEqual(
      expect.arrayContaining(["home", "playlist", "slide", "insert"]),
    );
    expect(tabs.find((tab) => tab.id === "playlist")?.label).toBe("Programação");
    expect(tabs.some((tab) => tab.id === "element")).toBe(false);
  });
});
