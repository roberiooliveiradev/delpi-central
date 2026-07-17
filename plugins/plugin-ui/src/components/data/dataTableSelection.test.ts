import { describe, expect, it } from "vitest";

import {
  primaryColumnKey,
  resolveCellSelection,
  resolveColumnSelection,
  resolveRowSelection,
  selectionFromColumnKey,
  selectionToTsv,
} from "./dataTableSelection";

describe("dataTableSelection", () => {
  const columns = ["a", "b", "c"];

  it("mapeia selectedColumnKey legado", () => {
    expect(selectionFromColumnKey("b")).toEqual({ kind: "column", keys: ["b"] });
    expect(primaryColumnKey({ kind: "column", keys: ["b", "c"] })).toBe("b");
  });

  it("suporta multi e range de colunas", () => {
    const base = resolveColumnSelection(null, "a", columns);
    expect(resolveColumnSelection(base, "c", columns, { toggle: true })).toEqual({
      kind: "column",
      keys: ["a", "c"],
    });
    expect(resolveColumnSelection(base, "c", columns, { range: true })).toEqual({
      kind: "column",
      keys: ["a", "b", "c"],
    });
  });

  it("seleciona linhas e células", () => {
    expect(resolveRowSelection(null, 2)).toEqual({ kind: "row", indices: [2] });
    expect(resolveRowSelection({ kind: "row", indices: [1] }, 3, { range: true })).toEqual({
      kind: "row",
      indices: [1, 2, 3],
    });
    expect(resolveCellSelection(null, { rowIndex: 0, columnKey: "a" })).toEqual({
      kind: "cell",
      cells: [{ rowIndex: 0, columnKey: "a" }],
    });
  });

  it("serializa seleção para TSV", () => {
    const rows = [
      { a: "1", b: "x" },
      { a: "2", b: "y" },
    ];
    expect(selectionToTsv({ kind: "column", keys: ["a"] }, rows, columns)).toBe("a\n1\n2");
    expect(
      selectionToTsv({ kind: "cell", cells: [{ rowIndex: 1, columnKey: "b" }] }, rows, columns),
    ).toBe("y");
  });
});
