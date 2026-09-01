import { describe, expect, it } from "vitest";

import {
  mapViewportRectToHostLocal,
  resolveCanvasTableSelectionOverlayRects,
  resolveCanvasTableTrackHandles,
} from "./canvasTableSelectionOverlay";

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

  it("usa âncora do merge quando coberta não tem td medido", () => {
    const mergedAnchorOnly = [
      { row: 0, col: 0, left: 0, top: 0, width: 90, height: 44 },
    ];
    const result = resolveCanvasTableSelectionOverlayRects({
      cellRects: mergedAnchorOnly,
      selectedCells: [
        { row: 0, col: 0 },
        { row: 0, col: 1 },
        { row: 1, col: 0 },
        { row: 1, col: 1 },
      ],
      focus: { row: 1, col: 1 },
      merges: [{ row: 0, col: 0, rowspan: 2, colspan: 2 }],
    });
    expect(result.range).toEqual({ left: 0, top: 0, width: 90, height: 44 });
    expect(result.focus).toEqual({ left: 0, top: 0, width: 90, height: 44 });
  });
});

describe("resolveCanvasTableTrackHandles", () => {
  const cellRects = [
    { row: 0, col: 0, left: 0, top: 0, width: 40, height: 20 },
    { row: 0, col: 1, left: 40, top: 0, width: 50, height: 20 },
    { row: 1, col: 0, left: 0, top: 20, width: 40, height: 24 },
    { row: 1, col: 1, left: 40, top: 20, width: 50, height: 24 },
  ];

  it("posiciona divisórias internas de coluna e linha", () => {
    const handles = resolveCanvasTableTrackHandles({ cellRects, rows: 2, cols: 2 });
    expect(handles).toEqual([
      { axis: "col", index: 0, left: 36, top: 0, width: 8, height: 44 },
      { axis: "row", index: 0, left: 0, top: 16, width: 90, height: 8 },
    ]);
  });

  it("não cria handle na última faixa", () => {
    expect(resolveCanvasTableTrackHandles({ cellRects, rows: 1, cols: 1 })).toEqual([]);
  });
});

describe("mapViewportRectToHostLocal", () => {
  it("compensa scale do palco (getBoundingClientRect ≠ offsetWidth)", () => {
    const local = mapViewportRectToHostLocal({
      hostRect: { left: 100, top: 50, width: 200, height: 100 },
      hostOffsetWidth: 400,
      hostOffsetHeight: 200,
      targetRect: { left: 150, top: 75, width: 50, height: 25 },
    });
    expect(local).toEqual({ left: 100, top: 50, width: 100, height: 50 });
  });

  it("escala 1:1 quando não há zoom", () => {
    const local = mapViewportRectToHostLocal({
      hostRect: { left: 10, top: 20, width: 100, height: 80 },
      hostOffsetWidth: 100,
      hostOffsetHeight: 80,
      targetRect: { left: 30, top: 40, width: 40, height: 20 },
    });
    expect(local).toEqual({ left: 20, top: 20, width: 40, height: 20 });
  });
});
