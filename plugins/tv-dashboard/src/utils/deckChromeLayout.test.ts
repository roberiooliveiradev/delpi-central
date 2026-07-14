import { afterEach, describe, expect, it } from "vitest";

import { readDeckChromeCollapsed, writeDeckChromeCollapsed } from "./deckChromeLayout";

describe("deckChromeLayout", () => {
  afterEach(() => {
    window.localStorage.removeItem("td-deck-chrome-collapsed");
  });

  it("default expandido", () => {
    expect(readDeckChromeCollapsed()).toBe(false);
  });

  it("persiste colapsado", () => {
    writeDeckChromeCollapsed(true);
    expect(readDeckChromeCollapsed()).toBe(true);
    writeDeckChromeCollapsed(false);
    expect(readDeckChromeCollapsed()).toBe(false);
  });
});
