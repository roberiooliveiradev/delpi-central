import { describe, expect, it } from "vitest";

import {
  resolveSelectionChromeColors,
  resolveSlideBackgroundSample,
  selectionChromeContrastCssVars,
} from "./selectionChromeContrast";

describe("selectionChromeContrast", () => {
  it("amostra cor sólida e média de gradiente", () => {
    expect(resolveSlideBackgroundSample({ type: "color", value: "#089bdb" })).toBe("#089bdb");
    const mid = resolveSlideBackgroundSample({
      type: "gradient",
      from: "#000000",
      to: "#ffffff",
    });
    expect(mid).toBe("#808080");
  });

  it("handles ocos: fill branco + borda que contraste com o fundo", () => {
    const colors = resolveSelectionChromeColors({ type: "color", value: "#089bdb" });
    expect(colors.handleFill.toLowerCase()).toBe("#ffffff");
    expect(colors.handleBorder).not.toBe(colors.handleFill);
    expect(colors.handleBorder.toLowerCase()).not.toBe("#089bdb");
  });

  it("em fundo branco: fill branco e borda accent da marca", () => {
    const colors = resolveSelectionChromeColors({ type: "color", value: "#ffffff" });
    expect(colors.handleFill.toLowerCase()).toBe("#ffffff");
    expect(colors.handleBorder.toLowerCase()).toBe("#089bdb");
    expect(colors.outline.toLowerCase()).toBe("#089bdb");
  });

  it("em fundo escuro: borda clara o suficiente contra o slide", () => {
    const colors = resolveSelectionChromeColors({ type: "color", value: "#0a3a52" }, "#089bdb");
    expect(colors.handleFill.toLowerCase()).toBe("#ffffff");
    expect(colors.handleBorder).not.toBe(colors.handleFill);
    expect(colors.handleBorder.toLowerCase()).not.toBe("#0a3a52");
  });

  it("parent hint e tokens CSS", () => {
    const colors = resolveSelectionChromeColors({ type: "color", value: "#ffffff" });
    expect(colors.parentHint).toMatch(/^#/);
    const vars = selectionChromeContrastCssVars(colors);
    expect(vars["--td-selection-handle-fill"]).toMatch(/^#/);
    expect(vars["--td-selection-outline"]).toMatch(/^#/);
    expect(vars["--td-selection-parent-hint"]).toMatch(/^#/);
  });
});
