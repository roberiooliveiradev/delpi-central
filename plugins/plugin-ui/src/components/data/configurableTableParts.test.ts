import { describe, expect, it } from "vitest";

import {
  deleteTablePart,
  isTablePartRefEqual,
  parseTablePartRef,
  partsToTableOptions,
  serializeTablePartRef,
  tableOptionsToParts,
  tablePartAllowsDelete,
  tablePartAllowsEdit,
} from "./configurableTableParts";

describe("configurableTableParts", () => {
  it("serializa e parseia refs de célula/cabeçalho", () => {
    expect(serializeTablePartRef({ kind: "title" })).toBe("title");
    expect(serializeTablePartRef({ kind: "headerCell", colIndex: 2 })).toBe("headerCell:2");
    expect(serializeTablePartRef({ kind: "cell", rowIndex: 1, colIndex: 3 })).toBe("cell:1:3");
    expect(parseTablePartRef("headerCell:2")).toEqual({ kind: "headerCell", colIndex: 2 });
    expect(parseTablePartRef("cell:1:3")).toEqual({ kind: "cell", rowIndex: 1, colIndex: 3 });
  });

  it("adapter options ↔ parts para título e cabeçalho", () => {
    const parts = tableOptionsToParts({ showTitle: false, showHeader: true, title: "OTD" });
    expect(parts.title?.visible).toBe(false);
    expect(parts.title?.content).toBe("OTD");
    expect(parts.header?.visible).toBe(true);
    expect(partsToTableOptions(parts)).toEqual({
      showTitle: false,
      title: "OTD",
      showHeader: true,
    });
  });

  it("capabilities: título editável/deletável; célula só selecionável", () => {
    expect(tablePartAllowsEdit({ kind: "title" })).toBe(true);
    expect(tablePartAllowsDelete({ kind: "header" })).toBe(true);
    expect(tablePartAllowsDelete({ kind: "cell", rowIndex: 0, colIndex: 0 })).toBe(false);
    expect(isTablePartRefEqual({ kind: "title" }, { kind: "title" })).toBe(true);
  });

  it("deleteTablePart oculta título e projeta options", () => {
    const result = deleteTablePart({}, { kind: "title" }, { title: "X", showTitle: true });
    expect(result.parts.title?.visible).toBe(false);
    expect(result.options.showTitle).toBe(false);
  });
});
