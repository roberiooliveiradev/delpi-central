import { describe, expect, it } from "vitest";

import {
  buildSeriesChartLayout,
  resolveVisibleXLabelIndices,
  resolveXLabelStep,
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
