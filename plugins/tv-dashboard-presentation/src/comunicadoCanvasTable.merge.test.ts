import { describe, expect, it } from "vitest";

import {
  applyCanvasTableMerge,
  canMergeRect,
  canvasTableCellHtmlSpan,
  expandSelectionToMerges,
  isCoveredCell,
  mergeAt,
  normalizeCanvasTableMerges,
  remapCanvasTableMerges,
  unmergeCanvasTableMerges,
} from "./canvasTableMerge";
import { createCanvasTableBlock, parseComunicadoConfig, serializeComunicadoConfig } from "./comunicadoHelpers";

const MERGE_2X2 = { row: 0, col: 0, rowspan: 2, colspan: 2 };

describe("canvas table merges", () => {
  it("faz merge 2×2 e unmerge restaura a âncora", () => {
    const cells = [
      { row: 0, col: 0 },
      { row: 0, col: 1 },
      { row: 1, col: 0 },
      { row: 1, col: 1 },
    ];
    expect(canMergeRect(cells, [])).toBe(true);
    const merged = applyCanvasTableMerge([], cells);
    expect(merged).toEqual([MERGE_2X2]);
    expect(isCoveredCell(merged, 1, 1)).toBe(true);
    expect(mergeAt(merged, 1, 1)).toEqual(MERGE_2X2);
    expect(unmergeCanvasTableMerges(merged, [{ row: 0, col: 0 }])).toEqual([]);
  });

  it("expande clique em coberta para o retângulo do merge", () => {
    expect(expandSelectionToMerges([{ row: 1, col: 1 }], [MERGE_2X2])).toEqual([
      { row: 1, col: 1 },
      { row: 0, col: 0 },
      { row: 0, col: 1 },
      { row: 1, col: 0 },
    ]);
  });

  it("rejeita overlap e seleção não retangular", () => {
    expect(
      canMergeRect(
        [
          { row: 0, col: 0 },
          { row: 0, col: 2 },
        ],
        [],
      ),
    ).toBe(false);
    expect(
      normalizeCanvasTableMerges(
        [MERGE_2X2, { row: 1, col: 1, rowspan: 2, colspan: 2 }],
        4,
        4,
      ),
    ).toEqual([MERGE_2X2]);
  });

  it("clampa merges inválidos ao reduzir rows", () => {
    expect(remapCanvasTableMerges([MERGE_2X2], 1, 4)).toEqual([]);
    expect(remapCanvasTableMerges([MERGE_2X2], 4, 1)).toEqual([]);
    expect(remapCanvasTableMerges([MERGE_2X2], 3, 3)).toEqual([MERGE_2X2]);
  });

  it("round-trip JSON preserva merges", () => {
    const created = createCanvasTableBlock(30, 0);
    const parsed = parseComunicadoConfig({
      blocks: [
        {
          ...created,
          rows: 3,
          cols: 3,
          cells: [["A", "B"], ["C"], ["D"]],
          merges: [MERGE_2X2],
        },
      ],
    });
    const block = parsed.blocks?.[0];
    expect(block?.type).toBe("canvas_table");
    if (block?.type !== "canvas_table") throw new Error("canvas_table");
    expect(block.merges).toEqual([MERGE_2X2]);
    const serialized = serializeComunicadoConfig(parsed);
    expect((serialized.blocks?.[0] as { merges?: unknown }).merges).toEqual([MERGE_2X2]);
  });

  it("âncora tem rowspan/colspan; coberta não gera span", () => {
    expect(canvasTableCellHtmlSpan([MERGE_2X2], 0, 0)).toEqual({ rowSpan: 2, colSpan: 2 });
    expect(canvasTableCellHtmlSpan([MERGE_2X2], 1, 1)).toEqual({});
    expect(isCoveredCell([MERGE_2X2], 1, 0)).toBe(true);
    expect(isCoveredCell([MERGE_2X2], 0, 0)).toBe(false);
  });
});
