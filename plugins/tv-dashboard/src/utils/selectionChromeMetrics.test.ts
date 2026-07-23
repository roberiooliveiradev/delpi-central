import { describe, expect, it } from "vitest";

import {
  SELECTION_CHROME_ZOOM_CEIL,
  SELECTION_CHROME_ZOOM_FLOOR,
  resolveSelectionChromeMetrics,
  selectionChromeCssVars,
} from "./selectionChromeMetrics";

describe("resolveSelectionChromeMetrics", () => {
  it("em 100% usa cantos 10px, pills e pad enxuto (4)", () => {
    const m = resolveSelectionChromeMetrics(1);
    expect(m.handleSize).toBe(10);
    expect(m.edgeLength).toBe(14);
    expect(m.edgeThickness).toBe(6);
    expect(m.outlineWidth).toBe(1.5);
    expect(m.selectionPad).toBe(4);
    expect(m.adjustSize).toBe(10);
    expect(m.rotateSize).toBe(18);
  });

  it("haste do giro deixa folga acima do pill N e do losango de ajuste", () => {
    const m = resolveSelectionChromeMetrics(1);
    /* Fundo do disco = -stem + rotateSize/2; topo do pill ≈ -edgeThickness. */
    const rotateBottom = -m.rotateStem + m.rotateSize / 2;
    const edgeChromeTop = -m.edgeThickness;
    const gap = edgeChromeTop - rotateBottom;
    expect(m.rotateStem).toBeGreaterThanOrEqual(30);
    expect(gap).toBeGreaterThanOrEqual(12);
  });

  it("haste desenhada para no topo do pill N sem atravessá-lo", () => {
    const m = resolveSelectionChromeMetrics(1);
    expect(m.rotateStemDraw).toBe(
      m.rotateStem - m.rotateSize / 2 - m.edgeThickness / 2,
    );
    const diskBottomY = -m.rotateStem + m.rotateSize / 2;
    const stemEndY = diskBottomY + m.rotateStemDraw;
    const pillTopY = -m.edgeThickness / 2;
    expect(stemEndY).toBeCloseTo(pillTopY, 5);
  });

  it("cresce em design px ao zoom out até o piso", () => {
    const at100 = resolveSelectionChromeMetrics(1);
    const atFloor = resolveSelectionChromeMetrics(SELECTION_CHROME_ZOOM_FLOOR);
    const belowFloor = resolveSelectionChromeMetrics(0.25);
    expect(atFloor.handleSize).toBeGreaterThan(at100.handleSize);
    expect(belowFloor.handleSize).toBe(atFloor.handleSize);
  });

  it("para de encolher acima do teto de zoom", () => {
    const atCeil = resolveSelectionChromeMetrics(SELECTION_CHROME_ZOOM_CEIL);
    const aboveCeil = resolveSelectionChromeMetrics(2);
    expect(aboveCeil.handleSize).toBe(atCeil.handleSize);
  });

  it("selectionChromeCssVars expõe tokens para o canvas", () => {
    const m = resolveSelectionChromeMetrics(1);
    const vars = selectionChromeCssVars(m);
    expect(vars["--td-selection-handle-size"]).toMatch(/px$/);
    expect(vars["--td-selection-edge-length"]).toMatch(/px$/);
    expect(vars["--td-selection-edge-thickness"]).toMatch(/px$/);
    expect(vars["--td-selection-outline-width"]).toMatch(/px$/);
    expect(vars["--td-global-selection-pad"]).toMatch(/px$/);
    expect(vars["--td-selection-rotate-stem"]).toBe(`${m.rotateStemDraw}px`);
  });
});
