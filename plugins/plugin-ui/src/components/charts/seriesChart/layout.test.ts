import { describe, expect, it } from "vitest";

import {
  buildSeriesChartLayout,
  resolveVisibleXLabelIndices,
  resolveXLabelStep,
  resolveXLabelTextAnchor,
  SERIES_CHART_PLOT_INSET,
} from "./layout";

describe("resolveVisibleXLabelIndices", () => {
  it("não empilha o último rótulo sobre o penúltimo tick do step", () => {
    // count=30, step=5 → 0,5,10,15,20,25; last=29 colide com 25 → substitui 25 por 29
    expect(resolveVisibleXLabelIndices(30, 5)).toEqual([0, 5, 10, 15, 20, 29]);
  });

  it("inclui o último quando a distância ao penúltimo é >= step", () => {
    expect(resolveVisibleXLabelIndices(11, 5)).toEqual([0, 5, 10]);
  });

  it("série curta com step 1 lista todos", () => {
    expect(resolveVisibleXLabelIndices(4, 1)).toEqual([0, 1, 2, 3]);
  });
});

describe("resolveXLabelTextAnchor", () => {
  it("ancora bordas para não cortar rótulos", () => {
    expect(resolveXLabelTextAnchor(0, 10, false)).toBe("start");
    expect(resolveXLabelTextAnchor(9, 10, false)).toBe("end");
    expect(resolveXLabelTextAnchor(4, 10, false)).toBe("middle");
  });

  it("rotacionado usa end", () => {
    expect(resolveXLabelTextAnchor(0, 10, true)).toBe("end");
  });
});

describe("buildSeriesChartLayout viewBox dinâmico", () => {
  it("respeita viewW/viewH informados", () => {
    const layout = buildSeriesChartLayout({
      points: [
        { value: 1, label: "a" },
        { value: 2, label: "b" },
      ],
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 800,
      viewH: 400,
    });
    expect(layout.viewW).toBe(800);
    expect(layout.viewH).toBe(400);
    expect(layout.visibleXLabelIndices.length).toBeGreaterThan(0);
  });

  it("inset mantém primeiro e último ponto dentro do plot", () => {
    const points = [
      { value: 40, label: "11/06/26" },
      { value: 70, label: "15/06/26" },
      { value: 100, label: "10/07/26" },
    ];
    const layout = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 600,
      viewH: 280,
    });
    expect(layout.plotInset).toBeGreaterThan(0);
    expect(layout.plotInset).toBeLessThanOrEqual(SERIES_CHART_PLOT_INSET);
    const x0 = layout.toX(0, points.length);
    const xLast = layout.toX(points.length - 1, points.length);
    const yMax = layout.toY(layout.axisMax);
    const yMin = layout.toY(layout.axisMin);
    expect(x0).toBeGreaterThanOrEqual(layout.margin.left + layout.plotInset - 0.01);
    expect(xLast).toBeLessThanOrEqual(layout.margin.left + layout.plotW - layout.plotInset + 0.01);
    expect(yMax).toBeGreaterThanOrEqual(layout.margin.top + layout.plotInset - 0.01);
    expect(yMin).toBeLessThanOrEqual(layout.margin.top + layout.plotH - layout.plotInset + 0.01);
  });

  it("step maior em plot estreito", () => {
    const labels = Array.from({ length: 40 }, (_, i) => `11/0${i}/26`);
    const step = resolveXLabelStep(40, 200, labels);
    expect(step).toBeGreaterThan(1);
    const indices = resolveVisibleXLabelIndices(40, step);
    for (let i = 1; i < indices.length; i += 1) {
      expect(indices[i]! - indices[i - 1]!).toBeGreaterThanOrEqual(1);
    }
  });
});
