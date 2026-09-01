import { describe, expect, it } from "vitest";

import {
  applyCanvasTableCellSelectionRequest,
  canvasTableCellRectangle,
  isCanvasTableCellSelected,
  primaryCanvasTableCellRef,
  summarizeCanvasTableCellSelection,
  type ComunicadoCanvasTableCellSelection,
} from "./canvasTableCellSelection";

describe("canvasTableCellSelection", () => {
  const blockId = "g1";

  it("clique simples substitui seleção", () => {
    const prev: ComunicadoCanvasTableCellSelection = {
      blockId,
      cells: [{ row: 0, col: 0 }],
      anchor: { row: 0, col: 0 },
      focus: { row: 0, col: 0 },
    };
    const next = applyCanvasTableCellSelectionRequest(prev, blockId, {
      cell: { row: 1, col: 2 },
      rowCount: 3,
      colCount: 3,
    });
    expect(next.cells).toEqual([{ row: 1, col: 2 }]);
    expect(next.anchor).toEqual({ row: 1, col: 2 });
  });

  it("band seleciona linha ou coluna inteira", () => {
    const rowBand = applyCanvasTableCellSelectionRequest(null, blockId, {
      cell: { row: 1, col: 0 },
      band: "row",
      rowCount: 3,
      colCount: 2,
    });
    expect(rowBand.cells).toEqual([
      { row: 1, col: 0 },
      { row: 1, col: 1 },
    ]);
    expect(rowBand.focus).toEqual({ row: 1, col: 0 });

    const colBand = applyCanvasTableCellSelectionRequest(null, blockId, {
      cell: { row: 0, col: 1 },
      band: "col",
      rowCount: 2,
      colCount: 2,
    });
    expect(colBand.cells).toEqual([
      { row: 0, col: 1 },
      { row: 1, col: 1 },
    ]);
  });

  it("Ctrl alterna célula na seleção", () => {
    const prev: ComunicadoCanvasTableCellSelection = {
      blockId,
      cells: [{ row: 0, col: 0 }],
      anchor: { row: 0, col: 0 },
      focus: { row: 0, col: 0 },
    };
    const added = applyCanvasTableCellSelectionRequest(prev, blockId, {
      cell: { row: 0, col: 1 },
      additive: true,
      rowCount: 3,
      colCount: 3,
    });
    expect(added.cells).toHaveLength(2);

    const removed = applyCanvasTableCellSelectionRequest(added, blockId, {
      cell: { row: 0, col: 0 },
      additive: true,
      rowCount: 3,
      colCount: 3,
    });
    expect(removed.cells).toEqual([{ row: 0, col: 1 }]);
  });

  it("Shift seleciona retângulo da âncora", () => {
    const prev: ComunicadoCanvasTableCellSelection = {
      blockId,
      cells: [{ row: 0, col: 0 }],
      anchor: { row: 0, col: 0 },
      focus: { row: 0, col: 0 },
    };
    const next = applyCanvasTableCellSelectionRequest(prev, blockId, {
      cell: { row: 1, col: 1 },
      range: true,
      rowCount: 3,
      colCount: 3,
    });
    expect(next.cells).toHaveLength(4);
    expect(isCanvasTableCellSelected(next, 0, 0)).toBe(true);
    expect(isCanvasTableCellSelected(next, 1, 1)).toBe(true);
  });

  it("retângulo inclusivo", () => {
    expect(
      canvasTableCellRectangle({ row: 2, col: 1 }, { row: 0, col: 2 }, 3, 4),
    ).toEqual([
      { row: 0, col: 1 },
      { row: 0, col: 2 },
      { row: 1, col: 1 },
      { row: 1, col: 2 },
      { row: 2, col: 1 },
      { row: 2, col: 2 },
    ]);
  });

  it("primary e rótulo de seleção", () => {
    const multi: ComunicadoCanvasTableCellSelection = {
      blockId,
      cells: [
        { row: 0, col: 0 },
        { row: 0, col: 1 },
      ],
      anchor: { row: 0, col: 0 },
      focus: { row: 0, col: 1 },
    };
    expect(primaryCanvasTableCellRef(multi)).toEqual({ row: 0, col: 1 });
    expect(summarizeCanvasTableCellSelection(multi)).toBe("2 células");
  });

  it("expande clique em coberta para o merge", () => {
    const next = applyCanvasTableCellSelectionRequest(null, blockId, {
      cell: { row: 1, col: 1 },
      rowCount: 3,
      colCount: 3,
      merges: [{ row: 0, col: 0, rowspan: 2, colspan: 2 }],
    });
    expect(next.cells).toHaveLength(4);
    expect(next.focus).toEqual({ row: 0, col: 0 });
    expect(isCanvasTableCellSelected(next, 0, 0)).toBe(true);
    expect(isCanvasTableCellSelected(next, 1, 1)).toBe(true);
  });
});
