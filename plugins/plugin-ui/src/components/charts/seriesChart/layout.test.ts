import { describe, expect, it } from "vitest";

import {
  buildSeriesChartLayout,
  chartPartFrameFromPlotLayout,
  resolveVisibleXLabelIndices,
  resolveXLabelStep,
  resolveXLabelTextAnchor,
  SERIES_CHART_PLOT_INSET,
} from "./layout";
import { OTD_SERIES_LAYOUT_GOLDEN as otdGolden } from "./__fixtures__/otdSeriesLayout.golden";

describe("resolveVisibleXLabelIndices", () => {
  it("não empilha o último rótulo sobre o penúltimo tick do step", () => {
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
      categoryPaddingPercent: 3,
    });
    expect(layout.plotInset).toBeGreaterThan(0);
    expect(layout.plotInset).toBeLessThanOrEqual(SERIES_CHART_PLOT_INSET * 4);
    const x0 = layout.toX(0, points.length);
    const xLast = layout.toX(points.length - 1, points.length);
    const yMax = layout.toY(layout.axisMax);
    const yMin = layout.toY(layout.axisMin);
    expect(x0).toBeGreaterThanOrEqual(layout.margin.left + layout.plotInset - 0.01);
    expect(xLast).toBeLessThanOrEqual(layout.margin.left + layout.plotW - layout.plotInset + 0.01);
    expect(yMax).toBeGreaterThanOrEqual(layout.margin.top + layout.plotInset - 0.01);
    expect(yMin).toBeLessThanOrEqual(layout.margin.top + layout.plotH - layout.plotInset + 0.01);
  });

  it("categoryPaddingPercent maior afasta os extremos", () => {
    const points = [
      { value: 10, label: "A" },
      { value: 20, label: "B" },
      { value: 30, label: "C" },
    ];
    const tight = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 200,
      categoryPaddingPercent: 2,
    });
    const loose = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 200,
      categoryPaddingPercent: 12,
    });
    expect(loose.plotInset).toBeGreaterThan(tight.plotInset);
    expect(loose.toX(0, 3)).toBeGreaterThan(tight.toX(0, 3));
  });

  it("plotFrame (4H.6) substitui margens automáticas", () => {
    const points = [
      { value: 10, label: "A" },
      { value: 20, label: "B" },
    ];
    const layout = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 200,
      plotFrame: { x: 10, y: 15, w: 70, h: 60 },
    });
    expect(layout.margin.left).toBeCloseTo(40, 5);
    expect(layout.margin.top).toBeCloseTo(30, 5);
    expect(layout.plotW).toBeCloseTo(280, 5);
    expect(layout.plotH).toBeCloseTo(120, 5);
    expect(layout.margin.right).toBeCloseTo(80, 5);
    expect(layout.margin.bottom).toBeCloseTo(50, 5);
  });

  it("chartPartFrameFromPlotLayout e marginsFromPlotFrame são inversos", () => {
    const auto = buildSeriesChartLayout({
      points: [
        { value: 1, label: "a" },
        { value: 2, label: "b" },
      ],
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 500,
      viewH: 250,
    });
    const frame = chartPartFrameFromPlotLayout(auto);
    const roundTrip = buildSeriesChartLayout({
      points: [
        { value: 1, label: "a" },
        { value: 2, label: "b" },
      ],
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 500,
      viewH: 250,
      plotFrame: frame,
    });
    expect(roundTrip.margin.left).toBeCloseTo(auto.margin.left, 4);
    expect(roundTrip.margin.top).toBeCloseTo(auto.margin.top, 4);
    expect(roundTrip.plotW).toBeCloseTo(auto.plotW, 4);
    expect(roundTrip.plotH).toBeCloseTo(auto.plotH, 4);
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

  it("tipografia maior aumenta margens e step (não quebra rótulos no resize)", () => {
    const points = Array.from({ length: 24 }, (_, i) => ({
      value: i + 1,
      label: `11/${String(i + 1).padStart(2, "0")}/26`,
    }));
    const small = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: true,
      viewW: 400,
      viewH: 220,
      typography: { axisFontSize: 9, axisTitleFontSize: 9 },
    });
    const large = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: true,
      viewW: 400,
      viewH: 220,
      typography: { axisFontSize: 28, axisTitleFontSize: 28 },
    });
    expect(large.margin.left).toBeGreaterThan(small.margin.left);
    expect(large.margin.bottom).toBeGreaterThan(small.margin.bottom);
    expect(large.xLabelStep).toBeGreaterThanOrEqual(small.xLabelStep);
  });
});

describe("golden layout fixture OTD", () => {
  it("snapshot estável: margens, inset e extremos sem clipping", () => {
    const layout = buildSeriesChartLayout({
      points: otdGolden.points,
      showXAxisLabels: otdGolden.showXAxisLabels,
      showXAxisTitle: otdGolden.showXAxisTitle,
      viewW: otdGolden.viewW,
      viewH: otdGolden.viewH,
      categoryPaddingPercent: otdGolden.categoryPaddingPercent,
    });
    const n = otdGolden.points.length;
    const snapshot = {
      margin: layout.margin,
      plotW: layout.plotW,
      plotH: layout.plotH,
      plotInset: layout.plotInset,
      x0: Number(layout.toX(0, n).toFixed(2)),
      xLast: Number(layout.toX(n - 1, n).toFixed(2)),
      yMin: Number(layout.toY(layout.axisMin).toFixed(2)),
      yMax: Number(layout.toY(layout.axisMax).toFixed(2)),
      firstAnchor: resolveXLabelTextAnchor(0, n, layout.xLabelsRotated),
      lastAnchor: resolveXLabelTextAnchor(n - 1, n, layout.xLabelsRotated),
    };

    expect(snapshot.x0).toBeGreaterThanOrEqual(snapshot.margin.left + snapshot.plotInset - 0.05);
    expect(snapshot.xLast).toBeLessThanOrEqual(
      snapshot.margin.left + snapshot.plotW - snapshot.plotInset + 0.05,
    );
    expect(snapshot.firstAnchor).toBe("start");
    expect(snapshot.lastAnchor).toBe("end");
    expect(snapshot.plotInset).toBeGreaterThanOrEqual(14);
    expect(snapshot.margin.right).toBeGreaterThanOrEqual(18);
    expect(snapshot.xLast - snapshot.x0).toBeGreaterThan(snapshot.plotW * 0.5);
  });
});
