import { describe, expect, it } from "vitest";

import {
  isContextualDeckRibbonTab,
  resolveDeckRibbonTabs,
  resolveEmbeddedComunicadoRibbonTabs,
  resolveSelectionPanelTabs,
} from "./deckRibbonTabMeta";

describe("deckRibbonTabMeta (Elemento / Tabela / Dados / Camadas)", () => {
  it("mostra abas Elemento, Dados e Camadas com seleção data-bound não-tabela", () => {
    const tabs = resolveDeckRibbonTabs(true, {
      hasSelection: true,
      isTableSelection: false,
      hasDataBoundSelection: true,
    });
    expect(tabs.map((tab) => tab.id)).toEqual(
      expect.arrayContaining(["element", "data", "layers"]),
    );
    expect(tabs.some((tab) => tab.id === "tableDesign")).toBe(false);
    expect(tabs.find((tab) => tab.id === "element")?.label).toBe("Elemento");
  });

  it("esconde Dados sem seleção data-bound (salvo showDataTab)", () => {
    const hidden = resolveDeckRibbonTabs(true, {
      hasSelection: true,
      hasDataBoundSelection: false,
    });
    expect(hidden.some((tab) => tab.id === "data")).toBe(false);

    const viaInsert = resolveDeckRibbonTabs(true, {
      hasSelection: true,
      hasDataBoundSelection: false,
      showDataTab: true,
    });
    expect(viaInsert.some((tab) => tab.id === "data")).toBe(true);
  });

  it("com tabela selecionada troca Elemento por Design + Layout", () => {
    const tabs = resolveDeckRibbonTabs(true, {
      hasSelection: true,
      isTableSelection: true,
      hasDataBoundSelection: true,
    });
    const ids = tabs.map((tab) => tab.id);
    expect(ids).toEqual(expect.arrayContaining(["tableDesign", "tableLayout", "data", "layers"]));
    expect(ids).not.toContain("element");
    expect(tabs.find((tab) => tab.id === "tableDesign")?.label).toBe("Design da Tabela");
    expect(tabs.find((tab) => tab.id === "tableLayout")?.label).toBe("Tabela Layout");
  });

  it("sem seleção mantém Camadas e esconde Elemento/Dados", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: false });
    expect(tabs.some((tab) => tab.id === "layers")).toBe(true);
    expect(tabs.some((tab) => tab.id === "element")).toBe(false);
    expect(tabs.some((tab) => tab.id === "data")).toBe(false);
    expect(isContextualDeckRibbonTab(tabs.find((t) => t.id === "layers")!)).toBe(true);
  });

  it("coloca contextuais depois das permanentes", () => {
    const tabs = resolveDeckRibbonTabs(true, {
      hasSelection: true,
      hasDataBoundSelection: true,
    });
    const ids = tabs.map((tab) => tab.id);
    const playlistIdx = ids.indexOf("playlist");
    const elementIdx = ids.indexOf("element");
    const layersIdx = ids.indexOf("layers");
    expect(playlistIdx).toBeGreaterThan(-1);
    expect(elementIdx).toBeGreaterThan(playlistIdx);
    expect(layersIdx).toBe(ids.length - 1);
    expect(isContextualDeckRibbonTab(tabs[layersIdx]!)).toBe(true);
    expect(isContextualDeckRibbonTab(tabs.find((t) => t.id === "insert")!)).toBe(false);
  });

  it("chrome embutido inclui Inserir, Exibir, Camadas e contextuais", () => {
    const both = resolveEmbeddedComunicadoRibbonTabs({
      hasSelection: true,
      hasDataBoundSelection: true,
    });
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
      hasDataBoundSelection: true,
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

  it("sempre inclui Programação, Inserir e Camadas em slide custom", () => {
    const tabs = resolveDeckRibbonTabs(true);
    expect(tabs.map((tab) => tab.id)).toEqual(
      expect.arrayContaining(["playlist", "slide", "insert", "layers"]),
    );
    expect(tabs.find((tab) => tab.id === "playlist")?.label).toBe("Programação");
    expect(tabs.some((tab) => tab.id === "element")).toBe(false);
    expect(tabs.some((tab) => tab.id === "home")).toBe(false);
  });

  it("painel lateral: só Camadas sem seleção; Elemento+Camadas com seleção", () => {
    expect(resolveSelectionPanelTabs({ hasSelection: false, showDataTab: false }).map((t) => t.id)).toEqual([
      "layers",
    ]);
    expect(
      resolveSelectionPanelTabs({ hasSelection: true, showDataTab: false }).map((t) => t.id),
    ).toEqual(["element", "layers"]);
    expect(
      resolveSelectionPanelTabs({ hasSelection: true, showDataTab: true }).map((t) => t.id),
    ).toEqual(["element", "data", "layers"]);
  });

  it("painel lateral: tabela espelha Design + Layout da top bar", () => {
    expect(
      resolveSelectionPanelTabs({
        hasSelection: true,
        showDataTab: false,
        isTableSelection: true,
      }).map((t) => t.id),
    ).toEqual(["tableDesign", "tableLayout", "layers"]);
    expect(
      resolveSelectionPanelTabs({
        hasSelection: true,
        showDataTab: true,
        isTableSelection: true,
      }).map((t) => ({ id: t.id, hasIcon: Boolean(t.icon) })),
    ).toEqual([
      { id: "tableDesign", hasIcon: true },
      { id: "tableLayout", hasIcon: true },
      { id: "data", hasIcon: true },
      { id: "layers", hasIcon: true },
    ]);
  });
});
