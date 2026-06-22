import { describe, expect, it } from "vitest";

import { csvCell, csvRow, sanitizeFilename, sanitizeSheetName } from "./primitives";
import { resolveDrawingExportActions } from "./dispatch";

describe("export primitives", () => {
  it("escapes csv cells with semicolon", () => {
    expect(csvCell('a;b')).toBe('"a;b"');
  });

  it("joins csv row with semicolon", () => {
    expect(csvRow(["a", 1])).toBe("a;1");
  });

  it("sanitizes filename with fallback", () => {
    expect(sanitizeFilename("***", "fallback")).toBe("fallback");
    expect(sanitizeFilename("Produtos programados")).toBe("Produtos_programados");
  });

  it("truncates long sheet names", () => {
    const longName = "A".repeat(40);
    expect(sanitizeSheetName(longName).length).toBeLessThanOrEqual(31);
  });
});

describe("resolveDrawingExportActions", () => {
  it("includes pdf and markdown when markdown exists", () => {
    const actions = resolveDrawingExportActions({ markdown: "# Relatório" });

    expect(actions.map((action) => action.format)).toEqual(["pdf", "markdown"]);
  });

  it("includes csv and xlsx when tables exist", () => {
    const actions = resolveDrawingExportActions({
      markdown: "# Relatório",
      tables: [
        {
          key: "t1",
          title: "Tabela",
          columns: [{ key: "a", label: "A" }],
          rows: [{ a: "1" }],
        },
      ],
    });

    expect(actions.some((action) => action.format === "csv")).toBe(true);
    expect(actions.some((action) => action.format === "xlsx")).toBe(true);
  });
});
