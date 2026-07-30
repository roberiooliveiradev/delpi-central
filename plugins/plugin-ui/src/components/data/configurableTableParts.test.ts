import { describe, expect, it } from "vitest";

import { DECK_TABLE_DEFAULTS } from "../../theme/deckColorCatalog";
import {
  deleteTablePart,
  isTablePartRefEqual,
  migrateLegacyTableChromeToFrame,
  parseTablePartRef,
  partsToTableOptions,
  resolveTableFrameStyle,
  resolveTableHeaderCellPaintStyle,
  resolveTablePartPaintStyle,
  resolveTableShapeChromePartRef,
  serializeTablePartRef,
  tableOptionsToParts,
  tablePartAllowsDelete,
  tablePartAllowsEdit,
  tablePartAllowsStroke,
  upsertTablePartState,
  applyTablePartStyleToSiblingParts,
  applyTablePartStyleToParts,
  resolveTableBodyCellPaintStyle,
} from "./configurableTableParts";

describe("configurableTableParts", () => {
  it("applyTablePartStyleToSiblingParts replica estilo em todas as células", () => {
    const next = applyTablePartStyleToSiblingParts(
      {},
      { kind: "cell", rowIndex: 0, colIndex: 0 },
      { fill: "#112233", color: "#fff" },
      { rowCount: 2, colCount: 2 },
    );
    expect(next["cell:0:0"]?.style?.fill).toBe("#112233");
    expect(next["cell:1:1"]?.style?.color).toBe("#fff");
    expect(next["headerCell:0"]).toBeUndefined();
  });

  it("applyTablePartStyleToSiblingParts replica em headerCells", () => {
    const next = applyTablePartStyleToSiblingParts(
      {},
      { kind: "headerCell", colIndex: 0 },
      { fill: "#0a0" },
      { rowCount: 1, colCount: 3 },
    );
    expect(next["headerCell:0"]?.style?.fill).toBe("#0a0");
    expect(next["headerCell:2"]?.style?.fill).toBe("#0a0");
  });
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
    expect(parts.frame?.style?.borderRadius).toBe(DECK_TABLE_DEFAULTS.borderRadius);
    expect(parts.frame?.style?.boxShadow).toBe(DECK_TABLE_DEFAULTS.boxShadow);
    expect(partsToTableOptions(parts)).toEqual({
      showTitle: false,
      title: "OTD",
      showHeader: true,
    });
  });

  it("resolveTableFrameStyle usa defaults Delpi e honra partes", () => {
    const defaults = resolveTableFrameStyle(undefined);
    expect(defaults.borderRadius).toBe(DECK_TABLE_DEFAULTS.borderRadius);
    expect(defaults.boxShadow).toBe(DECK_TABLE_DEFAULTS.boxShadow);
    expect(defaults.fill).toBe("#ffffff");
    expect(defaults.stroke).toBe("#b4b4b4");
    const custom = upsertTablePartState({}, { kind: "frame" }, {
      style: {
        fill: "#111111",
        stroke: "#ef4444",
        strokeWidth: 4,
        borderRadius: 12,
        boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
      },
    });
    expect(resolveTableFrameStyle(custom)).toEqual({
      fill: "#111111",
      stroke: "#ef4444",
      strokeWidth: 4,
      borderRadius: 12,
      boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
    });
  });

  it("resolveTableFrameStyle honra borderRadius 0 explícito e migra sombra legada", () => {
    const legacy = upsertTablePartState({}, { kind: "frame" }, {
      style: { fill: "#ffffff", stroke: "#b4b4b4", strokeWidth: 1, borderRadius: 0 },
    });
    const resolved = resolveTableFrameStyle(legacy);
    /* `borderRadius: 0` é cantos retos válidos — não reaplica default. */
    expect(resolved.borderRadius).toBe(0);
    expect(resolved.boxShadow).toBe(DECK_TABLE_DEFAULTS.boxShadow);
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

  it("resolveTableShapeChromePartRef mira a parte selecionada", () => {
    expect(resolveTableShapeChromePartRef(null)).toEqual({ kind: "frame" });
    expect(resolveTableShapeChromePartRef({ kind: "header" })).toEqual({ kind: "header" });
    expect(resolveTableShapeChromePartRef({ kind: "cell", rowIndex: 0, colIndex: 1 })).toEqual({
      kind: "cell",
      rowIndex: 0,
      colIndex: 1,
    });
    expect(tablePartAllowsStroke({ kind: "frame" })).toBe(true);
    expect(tablePartAllowsStroke({ kind: "title" })).toBe(false);
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

  it("serializa e parseia parte row", () => {
    expect(serializeTablePartRef({ kind: "row", rowIndex: 2 })).toBe("row:2");
    expect(parseTablePartRef("row:2")).toEqual({ kind: "row", rowIndex: 2 });
  });

  it("resolveTableBodyCellPaintStyle herda coluna → linha → célula", () => {
    let parts = upsertTablePartState({}, { kind: "headerCell", colIndex: 0 }, {
      style: { fill: "#aaa", fontFamily: "Inter", fontSize: 18 },
    });
    parts = upsertTablePartState(parts, { kind: "row", rowIndex: 1 }, {
      style: { color: "#111", fontWeight: "bold" },
    });
    parts = upsertTablePartState(parts, { kind: "cell", rowIndex: 1, colIndex: 0 }, {
      style: { fill: "#fff" },
    });
    expect(resolveTableBodyCellPaintStyle(parts, 1, 0)).toEqual({
      backgroundColor: "#fff",
      color: "#111",
      fontWeight: "bold",
      fontFamily: "Inter",
      fontSize: 18,
    });
  });

  it("applyTablePartStyleToParts aplica a várias colunas", () => {
    const next = applyTablePartStyleToParts(
      {},
      [
        { kind: "headerCell", colIndex: 0 },
        { kind: "headerCell", colIndex: 2 },
      ],
      { color: "#f00", fontSize: 22 },
    );
    expect(next["headerCell:0"]?.style).toMatchObject({ color: "#f00", fontSize: 22 });
    expect(next["headerCell:2"]?.style).toMatchObject({ color: "#f00", fontSize: 22 });
    expect(next["headerCell:1"]).toBeUndefined();
  });
});
