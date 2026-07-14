import { describe, expect, it } from "vitest";

import {
  chartFrameShortSidePx,
  resolveChartFloatToolbarMetrics,
} from "./chartFloatToolbarSize";

describe("resolveChartFloatToolbarMetrics", () => {
  it("aumenta a base vs. 32px fixo na referência", () => {
    const m = resolveChartFloatToolbarMetrics(320);
    expect(m.btnSize).toBe(40);
    expect(m.iconSize).toBe(20);
  });

  it("cresce com gráfico maior e respeita teto", () => {
    const mid = resolveChartFloatToolbarMetrics(480);
    const huge = resolveChartFloatToolbarMetrics(2000);
    expect(mid.btnSize).toBeGreaterThan(40);
    expect(huge.btnSize).toBe(56);
    expect(huge.iconSize).toBeLessThanOrEqual(28);
  });

  it("respeita piso em gráfico pequeno", () => {
    const m = resolveChartFloatToolbarMetrics(80);
    expect(m.btnSize).toBe(36);
    expect(m.iconSize).toBeGreaterThanOrEqual(16);
  });

  it("entrada inválida cai na referência", () => {
    expect(resolveChartFloatToolbarMetrics(Number.NaN).btnSize).toBe(40);
    expect(resolveChartFloatToolbarMetrics(0).btnSize).toBe(40);
  });
});

describe("chartFrameShortSidePx", () => {
  it("usa o menor lado em px de design", () => {
    expect(
      chartFrameShortSidePx({ w: 50, h: 40 }, { width: 1920, height: 1080 }),
    ).toBe(Math.min(960, 432));
  });
});
