import { describe, expect, it } from "vitest";

import {
  isContextualDeckRibbonTab,
  resolveDeckRibbonTabs,
  resolveEmbeddedComunicadoRibbonTabs,
} from "./deckRibbonTabMeta";

describe("deckRibbonTabMeta (Elemento / Dados / Camadas)", () => {
  it("mostra abas Elemento, Dados e Camadas com seleção", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: true });
    expect(tabs.map((tab) => tab.id)).toEqual(
      expect.arrayContaining(["element", "data", "layers"]),
    );
    expect(tabs.find((tab) => tab.id === "element")?.label).toBe("Elemento");
    expect(tabs.find((tab) => tab.id === "layers")?.label).toBe("Camadas");
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

  it("chrome embutido inclui Inserir, Exibir e as três contextuais", () => {
    const both = resolveEmbeddedComunicadoRibbonTabs({ hasSelection: true });
    expect(both.map((tab) => tab.id)).toEqual([
      "insert",
      "view",
      "element",
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
