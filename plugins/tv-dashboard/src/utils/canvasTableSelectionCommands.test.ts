import { describe, expect, it } from "vitest";

import { normalizeCanvasTableCell } from "@delpi/tv-dashboard-presentation";

import {
  applyCanvasTableMergeToBlock,
  clearCanvasTableSelectionContent,
  clearCanvasTableSelectionFormats,
  insertCanvasTableBand,
  patchCanvasTableCellsStyle,
} from "./canvasTableSelectionCommands";

function grid2x2() {
  return [
    [normalizeCanvasTableCell("A"), normalizeCanvasTableCell("B")],
    [normalizeCanvasTableCell("C"), normalizeCanvasTableCell("D")],
  ];
}

describe("canvasTableSelectionCommands", () => {
  it("patchCanvasTableCellsStyle aplica estilo em 2 células", () => {
    const cells = grid2x2();
    const next = patchCanvasTableCellsStyle({
      cells,
      selection: [
        { row: 0, col: 0 },
        { row: 1, col: 1 },
      ],
      stylePatch: { fontWeight: "bold", color: "#f00" },
    });
    expect(next[0]![0]!.style?.fontWeight).toBe("bold");
    expect(next[0]![0]!.style?.color).toBe("#f00");
    expect(next[1]![1]!.style?.fontWeight).toBe("bold");
    expect(next[0]![1]!.style?.fontWeight).toBeUndefined();
    expect(cells[0]![0]!.style).toBeUndefined();
  });

  it("applyCanvasTableMergeToBlock mescla e centraliza âncora", () => {
    const block = {
      id: "t1",
      type: "canvas_table" as const,
      rows: 2,
      cols: 2,
      cells: grid2x2(),
      frame: { x: 0, y: 0, w: 100, h: 80 },
    };
    const patch = applyCanvasTableMergeToBlock({
      block,
      selection: [
        { row: 0, col: 0 },
        { row: 0, col: 1 },
        { row: 1, col: 0 },
        { row: 1, col: 1 },
      ],
      mode: "merge",
    });
    expect(patch?.merges).toEqual([{ row: 0, col: 0, rowspan: 2, colspan: 2 }]);
    expect(patch?.cells?.[0]?.[0]?.style?.textAlign).toBe("center");
  });

  it("insertCanvasTableBand devolve patch de linhas", () => {
    const block = {
      id: "t1",
      type: "canvas_table" as const,
      rows: 2,
      cols: 2,
      cells: grid2x2(),
      frame: { x: 0, y: 0, w: 100, h: 80 },
    };
    const patch = insertCanvasTableBand({
      block,
      axis: "row",
      placement: "after",
      focus: { row: 0, col: 0 },
    });
    expect(patch.rows).toBe(3);
    expect(patch.cells?.length).toBe(3);
  });

  it("clear content e formats na seleção", () => {
    const cells = grid2x2();
    cells[0]![0] = {
      ...normalizeCanvasTableCell("X"),
      style: { color: "#00f", fontWeight: "bold" },
    };
    const cleared = clearCanvasTableSelectionContent({
      cells,
      selection: [{ row: 0, col: 0 }],
    });
    expect(cleared[0]![0]!.text).toBe("");
    expect(cleared[0]![0]!.style?.color).toBe("#00f");

    const formats = clearCanvasTableSelectionFormats({
      cells,
      selection: [{ row: 0, col: 0 }],
    });
    expect(formats[0]![0]!.text).toBe("X");
    expect(formats[0]![0]!.style).toBeUndefined();
  });
});
