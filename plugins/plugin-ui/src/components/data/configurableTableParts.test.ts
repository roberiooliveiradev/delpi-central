import { describe, expect, it } from "vitest";

import {
  deleteTablePart,
  isTablePartRefEqual,
  migrateLegacyTableChromeToFrame,
  parseTablePartRef,
  partsToTableOptions,
  resolveTableFrameStyle,
  resolveTableHeaderCellPaintStyle,
  resolveTablePartPaintStyle,
  serializeTablePartRef,
  tableOptionsToParts,
  tablePartAllowsDelete,
  tablePartAllowsEdit,
  upsertTablePartState,
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
    expect(parts.frame?.style?.borderRadius).toBe(0);
    expect(partsToTableOptions(parts)).toEqual({
      showTitle: false,
      title: "OTD",
      showHeader: true,
    });
  });

  it("resolveTableFrameStyle usa defaults Office e honra partes", () => {
    const defaults = resolveTableFrameStyle(undefined);
    expect(defaults.borderRadius).toBe(0);
    expect(defaults.fill).toBe("#ffffff");
    expect(defaults.stroke).toBe("#b4b4b4");
    const custom = upsertTablePartState({}, { kind: "frame" }, {
      style: { fill: "#111111", stroke: "#ef4444", strokeWidth: 4, borderRadius: 12 },
    });
    expect(resolveTableFrameStyle(custom)).toEqual({
      fill: "#111111",
      stroke: "#ef4444",
      strokeWidth: 4,
      borderRadius: 12,
    });
  });

  it("migrateLegacyTableChromeToFrame copia style legado sem sobrescrever frame", () => {
    const migrated = migrateLegacyTableChromeToFrame(undefined, {
      backgroundColor: "#abcabc",
      borderColor: "#123123",
      borderWidth: 3,
      borderRadius: 8,
    });
    expect(migrated.frame?.style?.fill).toBe("#abcabc");
    expect(migrated.frame?.style?.stroke).toBe("#123123");
    expect(migrated.frame?.style?.strokeWidth).toBe(3);
    expect(migrated.frame?.style?.borderRadius).toBe(8);

    const keep = migrateLegacyTableChromeToFrame(
      upsertTablePartState({}, { kind: "frame" }, { style: { fill: "#000000", borderRadius: 2 } }),
      { backgroundColor: "#ffffff", borderRadius: 99 },
    );
    expect(keep.frame?.style?.fill).toBe("#000000");
    expect(keep.frame?.style?.borderRadius).toBe(2);
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

  it("resolveTablePartPaintStyle e herança headerCell ← header", () => {
    const parts = upsertTablePartState({}, { kind: "header" }, {
      style: { fill: "#111111", color: "#eeeeee" },
    });
    const withCell = upsertTablePartState(parts, { kind: "headerCell", colIndex: 1 }, {
      style: { fill: "#222222" },
    });
    expect(resolveTablePartPaintStyle(withCell, { kind: "header" })).toEqual({
      backgroundColor: "#111111",
      color: "#eeeeee",
    });
    expect(resolveTableHeaderCellPaintStyle(withCell, 0)).toEqual({
      backgroundColor: "#111111",
      color: "#eeeeee",
    });
    expect(resolveTableHeaderCellPaintStyle(withCell, 1)).toEqual({
      backgroundColor: "#222222",
      color: "#eeeeee",
    });
  });
});
