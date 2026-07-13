import { describe, expect, it } from "vitest";

import { resolveTableFormatPaneTitle } from "./resolveTableFormatPaneTitle";

describe("resolveTableFormatPaneTitle", () => {
  it("usa Formatar Tabela sem parte", () => {
    expect(resolveTableFormatPaneTitle(null)).toBe("Formatar Tabela");
    expect(resolveTableFormatPaneTitle(undefined)).toBe("Formatar Tabela");
  });

  it("mapeia partes conhecidas", () => {
    expect(resolveTableFormatPaneTitle({ kind: "frame" })).toBe("Formatar Moldura");
    expect(resolveTableFormatPaneTitle({ kind: "title" })).toBe("Formatar Título da Tabela");
    expect(resolveTableFormatPaneTitle({ kind: "header" })).toBe("Formatar Cabeçalho");
    expect(resolveTableFormatPaneTitle({ kind: "headerCell", colIndex: 0 })).toBe(
      "Formatar Cabeçalho",
    );
    expect(resolveTableFormatPaneTitle({ kind: "cell", rowIndex: 1, colIndex: 2 })).toBe(
      "Formatar Célula",
    );
  });
});
