import { describe, expect, it } from "vitest";

import {
  DeckContentRunsView,
  plainTextFromDeckContentRuns,
  shouldPersistDeckContentRuns,
} from "../../index";

/**
 * TV presentation imports DeckContentRunsView from `@delpi/plugin-ui/index`.
 * Missing barrel export → React #130 (element type undefined) on home/editor.
 */
describe("deckContentRuns barrel export (index)", () => {
  it("expõe DeckContentRunsView como função de componente", () => {
    expect(typeof DeckContentRunsView).toBe("function");
  });

  it("expõe helpers de runs usados pelo editor TV", () => {
    expect(typeof plainTextFromDeckContentRuns).toBe("function");
    expect(typeof shouldPersistDeckContentRuns).toBe("function");
    expect(plainTextFromDeckContentRuns([{ text: "a" }, { text: "b" }])).toBe("ab");
    expect(shouldPersistDeckContentRuns([{ text: "x", style: { fontWeight: "bold" } }])).toBe(
      true,
    );
  });
});
