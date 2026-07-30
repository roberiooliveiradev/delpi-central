import { describe, expect, it } from "vitest";

import {
  SHAPE_CORNER_ADJUST_HANDLE,
  resolveAdjustmentChromeMinSeparationPx,
  separateAdjustmentHandleFromChromeControls,
} from "./selectionChromeAdjustSeparation";

describe("separateAdjustmentHandleFromChromeControls", () => {
  it("empurra ponto no NW para fora do handle de canto", () => {
    const next = separateAdjustmentHandleFromChromeControls({
      xPct: 0,
      yPct: 0,
      boxWidthPx: 400,
      boxHeightPx: 240,
      minSeparationPx: 16,
    });
    expect(next.x).toBeGreaterThan(0);
    expect(next.y).toBe(0);
    const dx = (next.x / 100) * 400;
    expect(Math.abs(dx)).toBeGreaterThanOrEqual(15.9);
  });

  it("não deixa o losango sob o pill N / giro (centro do topo)", () => {
    const next = separateAdjustmentHandleFromChromeControls({
      xPct: 50,
      yPct: 0,
      boxWidthPx: 400,
      boxHeightPx: 240,
      minSeparationPx: 16,
    });
    expect(next.y).toBe(0);
    const dx = ((next.x - 50) / 100) * 400;
    expect(Math.abs(dx)).toBeGreaterThanOrEqual(15.9);
  });

  it("preserva posição já afastada na borda superior (faixa de cantos)", () => {
    const x = SHAPE_CORNER_ADJUST_HANDLE.trackStartPct;
    const y = SHAPE_CORNER_ADJUST_HANDLE.yPct;
    const next = separateAdjustmentHandleFromChromeControls({
      xPct: x,
      yPct: y,
      boxWidthPx: 400,
      boxHeightPx: 240,
      minSeparationPx: 16,
    });
    expect(next.x).toBeCloseTo(x, 0);
    expect(next.y).toBe(0);
  });

  it("não empurra o losango de cantos para dentro do fill", () => {
    const next = separateAdjustmentHandleFromChromeControls({
      xPct: 8,
      yPct: 0,
      boxWidthPx: 200,
      boxHeightPx: 120,
      minSeparationPx: 16,
      lockTopEdge: true,
    });
    expect(next.y).toBe(0);
    expect(next.x).toBeGreaterThanOrEqual(8);
  });

  it("resolveAdjustmentChromeMinSeparationPx soma raios + folga", () => {
    expect(resolveAdjustmentChromeMinSeparationPx(10, 10, 6)).toBe(16);
  });
});

describe("SHAPE_CORNER_ADJUST_HANDLE", () => {
  it("ancora o losango na borda superior (y=0)", () => {
    expect(SHAPE_CORNER_ADJUST_HANDLE.yPct).toBe(0);
    expect(SHAPE_CORNER_ADJUST_HANDLE.trackStartPct).toBeLessThan(
      SHAPE_CORNER_ADJUST_HANDLE.trackEndPct,
    );
  });
});
