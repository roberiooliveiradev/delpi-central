import { describe, expect, it } from "vitest";

import { normalizeCanvasTableCell } from "@delpi/tv-dashboard-presentation";

import {
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
});
