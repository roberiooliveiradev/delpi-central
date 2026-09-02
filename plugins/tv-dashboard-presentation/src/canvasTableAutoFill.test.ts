import { describe, expect, it } from "vitest";

import {
  applyCanvasTableAutoFill,
  resolveCanvasTableAutoFillTarget,
  resolveCanvasTableBoundsOverlayRect,
  resolveCanvasTableCellAtHostPoint,
  resolveCanvasTableFillHandleRect,
} from "./canvasTableAutoFill";
import { normalizeCanvasTableCell } from "./comunicadoCanvasTable";

function textGrid(rows: string[][]) {
  return rows.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
}

describe("canvasTableAutoFill", () => {
  it("(a) série numérica unitária: 1 → baixo 3 células = 2,3,4", () => {
    const cells = textGrid([
      ["1", ""],
      ["", ""],
      ["", ""],
      ["", ""],
    ]);
    const target = resolveCanvasTableAutoFillTarget({
      sourceCells: [{ row: 0, col: 0 }],
      pointerCell: { row: 3, col: 0 },
      rows: 4,
      cols: 2,
    });
    expect(target?.direction).toBe("down");
    const filled = applyCanvasTableAutoFill({
      cells,
      sourceBounds: target!.sourceBounds,
      targetBounds: target!.targetBounds,
      direction: target!.direction,
    });
    expect(filled[1]?.[0]?.text).toBe("2");
    expect(filled[2]?.[0]?.text).toBe("3");
    expect(filled[3]?.[0]?.text).toBe("4");
  });

  it("(b) série com delta: 1|3 → baixo = 5,7", () => {
    const cells = textGrid([
      ["1"],
      ["3"],
      [""],
      [""],
    ]);
    const target = resolveCanvasTableAutoFillTarget({
      sourceCells: [
        { row: 0, col: 0 },
        { row: 1, col: 0 },
      ],
      pointerCell: { row: 3, col: 0 },
      rows: 4,
      cols: 1,
    });
    expect(target?.direction).toBe("down");
    const filled = applyCanvasTableAutoFill({
      cells,
      sourceBounds: target!.sourceBounds,
      targetBounds: target!.targetBounds,
      direction: target!.direction,
    });
    expect(filled[2]?.[0]?.text).toBe("5");
    expect(filled[3]?.[0]?.text).toBe("7");
  });

  it("(c) texto com sufixo numérico: Item 1 → Item 2", () => {
    const cells = textGrid([
      ["Item 1"],
      [""],
    ]);
    const target = resolveCanvasTableAutoFillTarget({
      sourceCells: [{ row: 0, col: 0 }],
      pointerCell: { row: 1, col: 0 },
      rows: 2,
      cols: 1,
    });
    const filled = applyCanvasTableAutoFill({
      cells,
      sourceBounds: target!.sourceBounds,
      targetBounds: target!.targetBounds,
      direction: target!.direction,
    });
    expect(filled[1]?.[0]?.text).toBe("Item 2");
  });

  it("(d) texto sem número → tile cópia", () => {
    const cells = textGrid([
      ["WEG", "x"],
      ["", ""],
    ]);
    cells[0]![0] = normalizeCanvasTableCell({
      kind: "text",
      text: "WEG",
      style: { backgroundColor: "#003366" },
    });
    const target = resolveCanvasTableAutoFillTarget({
      sourceCells: [{ row: 0, col: 0 }],
      pointerCell: { row: 1, col: 0 },
      rows: 2,
      cols: 2,
    });
    const filled = applyCanvasTableAutoFill({
      cells,
      sourceBounds: target!.sourceBounds,
      targetBounds: target!.targetBounds,
      direction: target!.direction,
    });
    expect(filled[1]?.[0]?.text).toBe("WEG");
    expect(filled[1]?.[0]?.style?.backgroundColor).toBe("#003366");
  });

  it("(e) clamp na última linha da grade", () => {
    const cells = textGrid([
      ["1"],
      [""],
      [""],
    ]);
    const target = resolveCanvasTableAutoFillTarget({
      sourceCells: [{ row: 0, col: 0 }],
      pointerCell: { row: 99, col: 0 },
      rows: 3,
      cols: 1,
    });
    expect(target?.targetBounds.rowMax).toBe(2);
    const filled = applyCanvasTableAutoFill({
      cells,
      sourceBounds: target!.sourceBounds,
      targetBounds: target!.targetBounds,
      direction: target!.direction,
    });
    expect(filled[1]?.[0]?.text).toBe("2");
    expect(filled[2]?.[0]?.text).toBe("3");
    expect(filled).toHaveLength(3);
  });

  it("(f) célula coberta por merge não recebe escrita", () => {
    const cells = textGrid([
      ["1", "x"],
      ["", ""],
      ["", ""],
    ]);
    const merges = [{ row: 1, col: 0, rowspan: 2, colspan: 1 }];
    const target = resolveCanvasTableAutoFillTarget({
      sourceCells: [{ row: 0, col: 0 }],
      pointerCell: { row: 2, col: 0 },
      rows: 3,
      cols: 2,
      merges,
    });
    const filled = applyCanvasTableAutoFill({
      cells,
      merges,
      sourceBounds: target!.sourceBounds,
      targetBounds: target!.targetBounds,
      direction: target!.direction,
    });
    // âncora do merge (1,0) recebe; coberta (2,0) permanece vazia
    expect(filled[1]?.[0]?.text).toBe("2");
    expect(filled[2]?.[0]?.text ?? "").toBe("");
  });

  it("(g) rect da alça no canto SE do range", () => {
    const handle = resolveCanvasTableFillHandleRect({
      range: { left: 10, top: 20, width: 100, height: 40 },
    });
    expect(handle).toEqual({
      left: 10 + 100 - 4,
      top: 20 + 40 - 4,
      width: 8,
      height: 8,
    });
    expect(resolveCanvasTableFillHandleRect({ range: null })).toBeNull();
  });

  it("hit-test encontra célula sob o ponto e preview une bounds", () => {
    const cellRects = [
      { row: 0, col: 0, left: 0, top: 0, width: 40, height: 20 },
      { row: 1, col: 0, left: 0, top: 20, width: 40, height: 24 },
    ];
    expect(resolveCanvasTableCellAtHostPoint({ cellRects, x: 10, y: 25 })).toEqual({
      row: 1,
      col: 0,
    });
    const preview = resolveCanvasTableBoundsOverlayRect({
      cellRects,
      bounds: { rowMin: 0, colMin: 0, rowMax: 1, colMax: 0 },
    });
    expect(preview).toEqual({ left: 0, top: 0, width: 40, height: 44 });
  });
});
