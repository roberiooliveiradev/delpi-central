import { describe, expect, it } from "vitest";

import { normalizeCanvasTableCell } from "@delpi/tv-dashboard-presentation";

import {
  buildCanvasTableDeletePatch,
  buildCanvasTableInsertPatch,
  resolveCanvasTableInsertFocus,
} from "./canvasTableStructureCommands";
import type { ComunicadoCanvasTableBlock } from "@delpi/tv-dashboard-presentation";

function sampleBlock(): ComunicadoCanvasTableBlock {
  return {
    id: "g1",
    type: "canvas_table",
    rows: 2,
    cols: 2,
    cells: [
      [normalizeCanvasTableCell("A"), normalizeCanvasTableCell("B")],
      [normalizeCanvasTableCell("C"), normalizeCanvasTableCell("D")],
    ],
    merges: [{ row: 0, col: 1, rowspan: 2, colspan: 1 }],
    canvasTableOptions: { columnWidths: [50, 50] },
    frame: { x: 0, y: 0, w: 40, h: 30 },
  };
}

describe("canvasTableStructureCommands", () => {
  it("resolve focus clampa e usa canto se ausente", () => {
    const block = sampleBlock();
    expect(resolveCanvasTableInsertFocus(block, { row: 9, col: -1 })).toEqual({
      row: 1,
      col: 0,
    });
    expect(resolveCanvasTableInsertFocus(block, null)).toEqual({ row: 1, col: 1 });
  });

  it("insere coluna à esquerda do foco e remapeia merges", () => {
    const patch = buildCanvasTableInsertPatch({
      block: sampleBlock(),
      axis: "col",
      placement: "before",
      focus: { row: 0, col: 1 },
    });
    expect(patch.cols).toBe(3);
    expect(patch.merges).toEqual([{ row: 0, col: 2, rowspan: 2, colspan: 1 }]);
  });

  it("exclui linha coberta e no-op em grade 1×N", () => {
    const block = sampleBlock();
    const deleted = buildCanvasTableDeletePatch({
      block,
      axis: "row",
      selection: [{ row: 0, col: 0 }],
    });
    expect(deleted?.rows).toBe(1);
    expect(deleted?.cells?.[0]?.[0]?.text).toBe("C");
    const single = { ...block, rows: 1, cells: [block.cells[0]!] };
    expect(
      buildCanvasTableDeletePatch({
        block: single,
        axis: "row",
        focus: { row: 0, col: 0 },
      }),
    ).toBeNull();
  });
});
