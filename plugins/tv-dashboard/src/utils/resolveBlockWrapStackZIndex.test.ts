import { describe, expect, it } from "vitest";

import {
  resolveBlockWrapStackZIndex,
  SELECTION_CHROME_STACK_FLOOR,
} from "./resolveBlockWrapStackZIndex";

describe("resolveBlockWrapStackZIndex", () => {
  it("sem chrome: preserva z do modelo", () => {
    expect(
      resolveBlockWrapStackZIndex({ modelZIndex: 7, selectionChromeVisible: false }),
    ).toBe(7);
  });

  it("com chrome: sobe acima de qualquer z de vizinho não selecionado", () => {
    const selected = resolveBlockWrapStackZIndex({
      modelZIndex: 2,
      selectionChromeVisible: true,
      isPrimarySelection: true,
    });
    const neighbor = resolveBlockWrapStackZIndex({
      modelZIndex: 99,
      selectionChromeVisible: false,
    });
    expect(selected).toBeGreaterThan(neighbor);
    expect(selected).toBeGreaterThan(SELECTION_CHROME_STACK_FLOOR);
  });

  it("primário fica acima de multi-selecionado secundário", () => {
    const primary = resolveBlockWrapStackZIndex({
      modelZIndex: 1,
      selectionChromeVisible: true,
      isPrimarySelection: true,
    });
    const secondary = resolveBlockWrapStackZIndex({
      modelZIndex: 50,
      selectionChromeVisible: true,
      isPrimarySelection: false,
    });
    expect(primary).toBeGreaterThan(secondary);
  });
});
