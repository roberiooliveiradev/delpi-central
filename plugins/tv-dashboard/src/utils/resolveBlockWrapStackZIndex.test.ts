import { describe, expect, it } from "vitest";

import {
  resolveBlockWrapStackZIndex,
  resolveSelectionChromeOverlayZIndex,
  resolveSelectionFloatToolbarOverlayZIndex,
  SELECTION_CHROME_STACK_FLOOR,
  SELECTION_FLOAT_TOOLBAR_STACK_FLOOR,
} from "./resolveBlockWrapStackZIndex";

describe("resolveBlockWrapStackZIndex", () => {
  it("sempre preserva z do modelo (seleção não eleva o conteúdo)", () => {
    expect(resolveBlockWrapStackZIndex({ modelZIndex: 7 })).toBe(7);
    expect(resolveBlockWrapStackZIndex({ modelZIndex: null })).toBe(1);
  });
});

describe("resolveSelectionChromeOverlayZIndex", () => {
  it("overlay fica acima de qualquer z de conteúdo do modelo", () => {
    const chrome = resolveSelectionChromeOverlayZIndex({
      modelZIndex: 2,
      isPrimarySelection: true,
    });
    const content = resolveBlockWrapStackZIndex({ modelZIndex: 99 });
    expect(chrome).toBeGreaterThan(content);
    expect(chrome).toBeGreaterThan(SELECTION_CHROME_STACK_FLOOR);
  });

  it("primário fica acima do multi-selecionado secundário", () => {
    const primary = resolveSelectionChromeOverlayZIndex({
      modelZIndex: 1,
      isPrimarySelection: true,
    });
    const secondary = resolveSelectionChromeOverlayZIndex({
      modelZIndex: 50,
      isPrimarySelection: false,
    });
    expect(primary).toBeGreaterThan(secondary);
  });
});

describe("resolveSelectionFloatToolbarOverlayZIndex", () => {
  it("float fica acima do chrome de seleção e do floor do group-chrome (13000)", () => {
    const chrome = resolveSelectionChromeOverlayZIndex({
      modelZIndex: 99,
      isPrimarySelection: true,
    });
    const floatZ = resolveSelectionFloatToolbarOverlayZIndex({ modelZIndex: 1 });
    expect(floatZ).toBeGreaterThan(chrome);
    expect(floatZ).toBeGreaterThan(13_000);
    expect(floatZ).toBeGreaterThanOrEqual(SELECTION_FLOAT_TOOLBAR_STACK_FLOOR);
  });
});
