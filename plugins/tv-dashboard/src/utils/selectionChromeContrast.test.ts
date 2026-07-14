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

  it("em fundo azul da marca, handles não usam o mesmo azul (perdem contraste)", () => {
    const colors = resolveSelectionChromeColors({ type: "color", value: "#089bdb" });
    expect(colors.handleFill.toLowerCase()).not.toBe("#089bdb");
    expect(colors.handleBorder).not.toBe(colors.handleFill);
  });

  it("em fundo branco mantém accent da marca quando há contraste", () => {
    const colors = resolveSelectionChromeColors({ type: "color", value: "#ffffff" });
    expect(colors.handleFill.toLowerCase()).toBe("#089bdb");
    expect(colors.handleBorder).toBe("#ffffff");
  });

  it("em fundo escuro usa chrome claro quando accent some", () => {
    const colors = resolveSelectionChromeColors({ type: "color", value: "#0a3a52" }, "#089bdb");
    // accent perto do fundo escuro/azulado — pick deve contrastar
    expect(colors.handleFill.toLowerCase()).not.toBe("#0a3a52");
    expect(colors.handleBorder).not.toBe(colors.handleFill);
  });

  it("selectionChromeContrastCssVars expõe tokens", () => {
    const vars = selectionChromeContrastCssVars(
      resolveSelectionChromeColors({ type: "color", value: "#ffffff" }),
    );
    expect(vars["--td-selection-handle-fill"]).toMatch(/^#/);
    expect(vars["--td-selection-outline"]).toMatch(/^#/);
  });
});
