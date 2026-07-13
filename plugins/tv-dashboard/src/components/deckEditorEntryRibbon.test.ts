import { describe, expect, it } from "vitest";

import { resolveDeckRibbonTabs } from "./deck/deckRibbonTabMeta";

describe("Deck editor entry ribbon", () => {
  it("sem seleção só exposa Page Home — Elemento fica oculto", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: false });
    expect(tabs.some((tab) => tab.id === "home")).toBe(true);
    expect(tabs.some((tab) => tab.id === "element")).toBe(false);
  });

  it("com seleção aparece Elemento (clique no palco / aba)", () => {
    const tabs = resolveDeckRibbonTabs(true, { hasSelection: true });
    expect(tabs.some((tab) => tab.id === "element")).toBe(true);
  });
});
