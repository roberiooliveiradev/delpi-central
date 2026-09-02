import { describe, expect, it } from "vitest";

import { readPanelFilters } from "../utils/panelFilterUrl";

describe("usePanelFilters search merge (preserva view)", () => {
  it("readPanelFilters sem view na query retorna table como default", () => {
    expect(readPanelFilters("?branch=01").view).toBe("table");
  });

  it("readPanelFilters com view=cards mantém cards", () => {
    expect(readPanelFilters("?branch=01&view=cards").view).toBe("cards");
  });
});
