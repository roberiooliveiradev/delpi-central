import { describe, expect, it } from "vitest";

import {
  canEditFormula,
  formatStepFormula,
  parseAddColumnFormula,
  parseFilterFormula,
  parseFormulaBarText,
  parseRenameFormula,
  parseSelectFormula,
  parseSortFormula,
} from "./dataTransformFormula";

describe("dataTransformFormula", () => {
  it("formata Fonte e addColumn", () => {
    expect(formatStepFormula(null)).toBe("= Fonte (rota api-delpi)");
    expect(
      formatStepFormula({ op: "addColumn", name: "gap", expr: "meta - oee" }),
    ).toBe("= AddColumn(Fonte, gap, meta - oee)");
  });

  it("parseAddColumn full e expr relativa", () => {
    expect(parseAddColumnFormula("= AddColumn(Fonte, gap, meta - oee)")).toEqual({
      ok: true,
      step: { op: "addColumn", name: "gap", expr: "meta - oee" },
    });
    expect(parseAddColumnFormula("meta - oee", { existingName: "gap" })).toEqual({
      ok: true,
      step: { op: "addColumn", name: "gap", expr: "meta - oee" },
    });
    expect(parseAddColumnFormula("meta - oee").ok).toBe(false);
  });

  it("parse rename / select / filter / sort", () => {
    expect(parseRenameFormula("= RenameColumns(Fonte, oee → oee_pct)")).toEqual({
      ok: true,
      step: { op: "rename", from: "oee", to: "oee_pct" },
    });
    expect(parseSelectFormula("= SelectColumns(Fonte, [a, b])")).toEqual({
      ok: true,
      step: { op: "select", columns: ["a", "b"] },
    });
    expect(parseFilterFormula("= FilterRows(Fonte, branch is not null)")).toEqual({
      ok: true,
      step: { op: "filter", column: "branch", cmp: "notNull" },
    });
    expect(parseFilterFormula('= FilterRows(Fonte, [branch] eq "01")')).toEqual({
      ok: true,
      step: { op: "filter", column: "branch", cmp: "eq", value: "01" },
    });
    expect(parseSortFormula("= Sort(Fonte, oee, desc)")).toEqual({
      ok: true,
      step: { op: "sort", column: "oee", direction: "desc" },
    });
  });

  it("edita filter/sort pela barra com contexto de etapa", () => {
    expect(
      parseFormulaBarText('= FilterRows(Fonte, [branch] eq "02")', {
        step: { op: "filter", column: "branch", cmp: "eq", value: "01" },
      }),
    ).toEqual({
      ok: true,
      step: { op: "filter", column: "branch", cmp: "eq", value: "02" },
    });
    expect(
      parseFormulaBarText("= Sort(Fonte, meta, asc)", {
        step: { op: "sort", column: "oee", direction: "desc" },
      }),
    ).toEqual({
      ok: true,
      step: { op: "sort", column: "meta", direction: "asc" },
    });
  });

  it("canEditFormula e parseFormulaBarText por contexto", () => {
    expect(canEditFormula({ op: "addColumn", name: "a", expr: "1" })).toBe(true);
    expect(canEditFormula({ op: "merge", sourceId: "x", leftKey: "a", rightKey: "b" })).toBe(
      false,
    );
    const parsed = parseFormulaBarText("= AddColumn(Fonte, x, 1 + 2)", {
      step: null,
      newColumnDraft: true,
    });
    expect(parsed).toEqual({
      ok: true,
      step: { op: "addColumn", name: "x", expr: "1 + 2" },
    });
  });
});
