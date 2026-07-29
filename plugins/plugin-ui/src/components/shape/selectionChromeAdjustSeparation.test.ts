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
    expect(next.y).toBeGreaterThan(0);
    const dx = (next.x / 100) * 400;
    const dy = (next.y / 100) * 240;
    expect(Math.hypot(dx, dy)).toBeGreaterThanOrEqual(15.9);
  });

  it("não deixa o losango sob o pill N / giro (centro do topo)", () => {
    const next = separateAdjustmentHandleFromChromeControls({
      xPct: 50,
      yPct: 0,
      boxWidthPx: 400,
      boxHeightPx: 240,
      minSeparationPx: 16,
    });
    const dx = ((next.x - 50) / 100) * 400;
    const dy = ((next.y - 0) / 100) * 240;
    expect(Math.hypot(dx, dy)).toBeGreaterThanOrEqual(15.9);
  });

  it("preserva posição já afastada (faixa de cantos)", () => {
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
    expect(next.y).toBeCloseTo(y, 0);
  });

  it("resolveAdjustmentChromeMinSeparationPx soma raios + folga", () => {
    expect(resolveAdjustmentChromeMinSeparationPx(10, 10, 6)).toBe(16);
  });
});
