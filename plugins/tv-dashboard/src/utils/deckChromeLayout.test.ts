import { afterEach, describe, expect, it } from "vitest";

import { clearLegacyDeckChromeCollapsed } from "./deckChromeLayout";

afterEach(() => {
  window.localStorage.clear();
});

describe("deckChromeLayout", () => {
  it("limpa preferência legada de chrome recolhido", () => {
    window.localStorage.setItem("td-deck-chrome-collapsed", "1");
    clearLegacyDeckChromeCollapsed();
    expect(window.localStorage.getItem("td-deck-chrome-collapsed")).toBeNull();
  });
});
