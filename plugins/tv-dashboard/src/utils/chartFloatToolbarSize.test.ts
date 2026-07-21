import { describe, expect, it } from "vitest";

import {
  complexFrameShortSidePx,
  resolveComplexFloatToolbarMetrics,
} from "./complexFloatToolbarSize";
import {
  chartFrameShortSidePx,
  resolveChartFloatToolbarMetrics,
} from "./chartFloatToolbarSize";

describe("resolveComplexFloatToolbarMetrics", () => {
  it("aumenta a base vs. 32px fixo na referência", () => {
    const m = resolveComplexFloatToolbarMetrics(320);
    expect(m.btnSize).toBe(40);
    expect(m.iconSize).toBe(20);
  });

  it("cresce com bloco maior e respeita teto", () => {
    const mid = resolveComplexFloatToolbarMetrics(480);
    const huge = resolveComplexFloatToolbarMetrics(2000);
    expect(mid.btnSize).toBeGreaterThan(40);
    expect(huge.btnSize).toBe(56);
    expect(huge.iconSize).toBeLessThanOrEqual(28);
  });

  it("respeita piso em bloco pequeno", () => {
    const m = resolveComplexFloatToolbarMetrics(80);
    expect(m.btnSize).toBe(36);
    expect(m.iconSize).toBeGreaterThanOrEqual(16);
    expect(m.offset).toBeGreaterThanOrEqual(20);
  });

  it("entrada inválida cai na referência", () => {
    expect(resolveComplexFloatToolbarMetrics(Number.NaN).btnSize).toBe(40);
    expect(resolveComplexFloatToolbarMetrics(0).btnSize).toBe(40);
  });

  it("aliases chart* permanecem equivalentes", () => {
    expect(resolveChartFloatToolbarMetrics(320)).toEqual(resolveComplexFloatToolbarMetrics(320));
    expect(
      chartFrameShortSidePx({ w: 50, h: 40 }, { width: 1920, height: 1080 }),
    ).toBe(complexFrameShortSidePx({ w: 50, h: 40 }, { width: 1920, height: 1080 }));
  });
});

describe("complexFrameShortSidePx", () => {
  it("usa o menor lado em px de design", () => {
    expect(
      complexFrameShortSidePx({ w: 50, h: 40 }, { width: 1920, height: 1080 }),
    ).toBe(Math.min(960, 432));
  });
});
