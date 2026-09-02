import { describe, expect, it } from "vitest";

import {
  autoFitCanvasTableTrack,
  canvasTableBandSelection,
  canvasTableTrackContentWeights,
  insertCanvasTableCol,
  insertCanvasTableRow,
} from "./canvasTableStructure";
import { normalizeCanvasTableCell } from "./comunicadoCanvasTable";

describe("canvasTableStructure", () => {
  it("insere coluna à esquerda e desloca merges", () => {
    const result = insertCanvasTableCol({
      cells: [
        [normalizeCanvasTableCell("A"), normalizeCanvasTableCell("B")],
        [normalizeCanvasTableCell("C"), normalizeCanvasTableCell("D")],
      ],
      rows: 2,
      cols: 2,
      at: 1,
      placement: "before",
      merges: [{ row: 0, col: 1, rowspan: 2, colspan: 1 }],
      columnWidths: [50, 50],
    });
    expect(result.cols).toBe(3);
    expect(result.cells[0]?.[1]?.text).toBe("");
    expect(result.cells[0]?.[2]?.text).toBe("B");
    expect(result.merges).toEqual([{ row: 0, col: 2, rowspan: 2, colspan: 1 }]);
    expect(result.columnWidths.reduce((s, n) => s + n, 0)).toBeCloseTo(100, 5);
  });

  it("insere linha abaixo e estende merge atravessado", () => {
    const result = insertCanvasTableRow({
      cells: [
        [normalizeCanvasTableCell("A"), normalizeCanvasTableCell("B")],
        [normalizeCanvasTableCell("C"), normalizeCanvasTableCell("D")],
      ],
      rows: 2,
      cols: 2,
      at: 0,
      placement: "after",
      merges: [{ row: 0, col: 0, rowspan: 2, colspan: 1 }],
    });
    expect(result.rows).toBe(3);
    expect(result.merges[0]?.rowspan).toBe(3);
  });

  it("auto-fit soma 100 e respeita mínimo", () => {
    const next = autoFitCanvasTableTrack({
      tracks: [25, 25, 25, 25],
      index: 0,
      contentWeights: [10, 1, 1, 1],
    });
    expect(next).toHaveLength(4);
    expect(next.reduce((s, n) => s + n, 0)).toBeCloseTo(100, 5);
    next.forEach((item) => expect(item).toBeGreaterThanOrEqual(4));
    expect(next[0]).toBeGreaterThan(next[1]!);
  });

  it("gutter seleciona faixa inteira", () => {
    expect(canvasTableBandSelection({ axis: "row", index: 1, rows: 3, cols: 2 })).toEqual([
      { row: 1, col: 0 },
      { row: 1, col: 1 },
    ]);
    expect(canvasTableBandSelection({ axis: "col", index: 0, rows: 2, cols: 2 })).toEqual([
      { row: 0, col: 0 },
      { row: 1, col: 0 },
    ]);
  });

  it("pesos de conteúdo priorizam coluna com texto longo", () => {
    const weights = canvasTableTrackContentWeights({
      axis: "col",
      rows: 1,
      cols: 2,
      cells: [[normalizeCanvasTableCell("A"), normalizeCanvasTableCell("ABCDEFGHIJ")]],
    });
    expect(weights[1]).toBeGreaterThan(weights[0]!);
  });

  it("pesos de cellRects priorizam faixa mais larga e autofit normaliza 100%", () => {
    const weights = canvasTableTrackRectWeights({
      axis: "col",
      rows: 1,
      cols: 3,
      cellRects: [
        { row: 0, col: 0, width: 40, height: 20 },
        { row: 0, col: 1, width: 120, height: 20 },
        { row: 0, col: 2, width: 40, height: 20 },
      ],
    });
    expect(weights).not.toBeNull();
    expect(weights![1]).toBeGreaterThan(weights![0]!);
    expect(canvasTableTrackRectWeights({ axis: "col", rows: 2, cols: 2, cellRects: [] })).toBeNull();
    const next = autoFitCanvasTableTrack({
      tracks: [33, 34, 33],
      index: 1,
      contentWeights: weights!,
    });
    expect(next.reduce((s, n) => s + n, 0)).toBeCloseTo(100, 5);
    expect(next[1]).toBeGreaterThan(next[0]!);
  });
});
