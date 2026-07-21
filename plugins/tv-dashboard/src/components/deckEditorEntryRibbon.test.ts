import { describe, expect, it } from "vitest";

import { resolveDeckRibbonTabs } from "./deck/deckRibbonTabMeta";

describe("Deck editor entry ribbon", () => {
  it("sem seleção: Inserir/Programação visíveis; sem Elemento nem home", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: false });
    expect(tabs.some((tab) => tab.id === "insert")).toBe(true);
    expect(tabs.some((tab) => tab.id === "playlist")).toBe(true);
    expect(tabs.some((tab) => tab.id === "home")).toBe(false);
    expect(tabs.some((tab) => tab.id === "element")).toBe(false);
  });

  it("com seleção aparece Elemento (clique no palco / aba)", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: true });
    expect(tabs.some((tab) => tab.id === "element")).toBe(true);
  });
});
