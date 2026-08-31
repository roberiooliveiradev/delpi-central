import { describe, expect, it } from "vitest";

import { resolveCanvasTableSelectionOverlayRects } from "./canvasTableSelectionOverlay";

describe("resolveCanvasTableSelectionOverlayRects", () => {
  const cellRects = [
    { row: 0, col: 0, left: 0, top: 0, width: 40, height: 20 },
    { row: 0, col: 1, left: 40, top: 0, width: 50, height: 20 },
    { row: 1, col: 0, left: 0, top: 20, width: 40, height: 24 },
    { row: 1, col: 1, left: 40, top: 20, width: 50, height: 24 },
  ];

  it("retorna null sem seleção", () => {
    expect(
      resolveCanvasTableSelectionOverlayRects({
        cellRects,
        selectedCells: [],
      }),
    ).toEqual({ range: null, focus: null });
  });

  it("une o retângulo de uma célula", () => {
    const result = resolveCanvasTableSelectionOverlayRects({
      cellRects,
      selectedCells: [{ row: 0, col: 1 }],
    });
    expect(result.range).toEqual({ left: 40, top: 0, width: 50, height: 20 });
    expect(result.focus).toEqual({ left: 40, top: 0, width: 50, height: 20 });
  });

  it("une o retângulo de um range 2x2", () => {
    const result = resolveCanvasTableSelectionOverlayRects({
      cellRects,
      selectedCells: [
        { row: 0, col: 0 },
        { row: 0, col: 1 },
        { row: 1, col: 0 },
        { row: 1, col: 1 },
      ],
      focus: { row: 1, col: 1 },
    });
    expect(result.range).toEqual({ left: 0, top: 0, width: 90, height: 44 });
    expect(result.focus).toEqual({ left: 40, top: 20, width: 50, height: 24 });
  });

  it("ignora células sem rect medido", () => {
    const result = resolveCanvasTableSelectionOverlayRects({
      cellRects,
      selectedCells: [
        { row: 0, col: 0 },
        { row: 9, col: 9 },
      ],
    });
    expect(result.range).toEqual({ left: 0, top: 0, width: 40, height: 20 });
  });
});
