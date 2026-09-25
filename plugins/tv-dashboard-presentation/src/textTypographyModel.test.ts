import { describe, expect, it } from "vitest";

import { contentRunStyleToCss } from "./comunicadoContentRuns";
import {
  bumpFontSizeValue,
  clampIndentLevel,
  indentPaddingPx,
  transformContentRunsCase,
  transformTextCase,
} from "./textTypographyModel";

describe("textTypographyModel", () => {
  it("transformTextCase cobre modos canônicos pt-BR", () => {
    expect(transformTextCase("olá mundo. teste", "sentence")).toBe("Olá mundo. teste");
    expect(transformTextCase("Olá Mundo", "lower")).toBe("olá mundo");
    expect(transformTextCase("olá mundo", "upper")).toBe("OLÁ MUNDO");
    expect(transformTextCase("olá mundo lindo", "title")).toBe("Olá Mundo Lindo");
    expect(transformTextCase("Olá", "toggle")).toBe("oLÁ");
  });

  it("transformContentRunsCase preserva dataRef atômico", () => {
    const runs = [
      { text: "meta " },
      { text: "…", dataRef: { field: "filter.end_date" } },
      { text: " fim" },
    ];
    const next = transformContentRunsCase(runs, "upper");
    expect(next[0]?.text).toBe("META ");
    expect(next[1]?.dataRef?.field).toBe("filter.end_date");
    expect(next[1]?.text).toBe("…");
    expect(next[2]?.text).toBe(" FIM");
  });

  it("bumpFontSizeValue e indent clamp", () => {
    expect(bumpFontSizeValue(28, 1)).toBe(30);
    expect(bumpFontSizeValue(28, -1)).toBe(26);
    expect(clampIndentLevel(99)).toBe(8);
    expect(indentPaddingPx(2)).toBe(48);
  });

  it("contentRunStyleToCss aplica baselineShift e indent", () => {
    const css = contentRunStyleToCss({
      baselineShift: "super",
      indentLevel: 1,
      fontSize: 24,
    });
    expect(css.verticalAlign).toBe("super");
    expect(css.paddingLeft).toBe("24px");
    expect(css.fontSize).toBe("24px");
  });
});
