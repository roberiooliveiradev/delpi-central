import { describe, expect, it } from "vitest";

import {
  SELECTION_CHROME_ZOOM_CEIL,
  SELECTION_CHROME_ZOOM_FLOOR,
  resolveSelectionChromeMetrics,
  selectionChromeCssVars,
} from "./selectionChromeMetrics";

describe("resolveSelectionChromeMetrics", () => {
  it("em 100% usa base maior que o chrome antigo (12/1)", () => {
    const m = resolveSelectionChromeMetrics(1);
    expect(m.handleSize).toBeGreaterThanOrEqual(16);
    expect(m.outlineWidth).toBeGreaterThanOrEqual(2);
    expect(m.adjustSize).toBe(m.handleSize);
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
    const vars = selectionChromeCssVars(resolveSelectionChromeMetrics(1));
    expect(vars["--td-selection-handle-size"]).toMatch(/px$/);
    expect(vars["--td-selection-outline-width"]).toMatch(/px$/);
    expect(vars["--td-global-selection-pad"]).toMatch(/px$/);
  });
});
