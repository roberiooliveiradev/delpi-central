import { describe, expect, it } from "vitest";

import {
  buildSeriesChartLayout,
  chartPartFrameFromPlotLayout,
  resolveHorizontalCategoryLabelLeftPad,
  resolveSeriesChartCategoryBarSlot,
  resolveSeriesChartCategoryScale,
  resolveVisibleXLabelIndices,
  resolveXLabelStep,
  resolveXLabelTextAnchor,
  resolveYAxisTitleAnchorX,
  SERIES_CHART_MIN_PLOT_FRACTION,
  SERIES_CHART_MIN_PLOT_PX,
  yAxisTitleGutterPx,
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

  it("centeredPlot usa margens simétricas (pizza/funil/radar)", () => {
    const layout = buildSeriesChartLayout({
      points: [
        { value: 12, label: "LMP" },
        { value: 2, label: "AMOSTRA" },
      ],
      showXAxisLabels: true,
      showXAxisTitle: true,
      viewW: 280,
      viewH: 200,
      centeredPlot: true,
    });
    expect(layout.margin.left).toBe(layout.margin.right);
    expect(layout.margin.top).toBe(layout.margin.bottom);
    const cx = layout.margin.left + layout.plotW / 2;
    const cy = layout.margin.top + layout.plotH / 2;
    expect(cx).toBeCloseTo(layout.viewW / 2, 5);
    expect(cy).toBeCloseTo(layout.viewH / 2, 5);
  });

  it("sem padding: primeiro e último ponto nas bordas do plot", () => {
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
      categoryPaddingPercent: 0,
    });
    expect(layout.plotInset).toBe(0);
    const x0 = layout.toX(0, points.length);
    const xLast = layout.toX(points.length - 1, points.length);
    const yMax = layout.toY(layout.axisMax);
    const yMin = layout.toY(layout.axisMin);
    expect(x0).toBeCloseTo(layout.margin.left, 5);
    expect(xLast).toBeCloseTo(layout.margin.left + layout.plotW, 5);
    expect(yMax).toBeGreaterThanOrEqual(layout.margin.top - 0.01);
    expect(yMin).toBeLessThanOrEqual(layout.margin.top + layout.plotH + 0.01);
    expect(yMin).toBeCloseTo(layout.margin.top + layout.plotH, 5);
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

  it("showYAxisTitle reserva margem esquerda e âncora cabe no viewBox", () => {
    const points = [
      { value: 70, label: "01/07/26" },
      { value: 90, label: "15/07/26" },
      { value: 110, label: "28/07/26" },
    ];
    const without = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: true,
      showYAxisTitle: false,
      viewW: 400,
      viewH: 220,
      typography: { axisFontSize: 14, axisTitleFontSize: 22 },
    });
    const withTitle = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: true,
      showYAxisTitle: true,
      viewW: 400,
      viewH: 220,
      typography: { axisFontSize: 14, axisTitleFontSize: 22 },
    });
    expect(withTitle.margin.left).toBeGreaterThan(without.margin.left);
    const anchor = resolveYAxisTitleAnchorX(withTitle.margin.left, 22);
    expect(anchor - 22 * 0.55).toBeGreaterThanOrEqual(2);
    expect(anchor).toBeLessThan(withTitle.margin.left);
  });

  it("plotFrame apertado ainda respeita piso de gutter do título Y", () => {
    const layout = buildSeriesChartLayout({
      points: [
        { value: 1, label: "a" },
        { value: 2, label: "b" },
      ],
      showXAxisLabels: true,
      showXAxisTitle: false,
      showYAxisTitle: true,
      viewW: 400,
      viewH: 220,
      plotFrame: { x: 2, y: 5, w: 90, h: 80 },
      typography: { axisFontSize: 14, axisTitleFontSize: 20 },
    });
    expect(layout.margin.left).toBeGreaterThanOrEqual(yAxisTitleGutterPx(20) + Math.round(14 * 2.6));
  });

  it("tipografia extrema no resize mantém plot utilizável (não blank)", () => {
    const points = Array.from({ length: 14 }, (_, i) => ({
      value: 60 + i,
      label: `${String(i + 1).padStart(2, "0")}/07/26`,
    }));
    const layout = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: true,
      viewW: 360,
      viewH: 200,
      typography: { axisFontSize: 48, axisTitleFontSize: 44 },
    });
    expect(layout.plotW).toBeGreaterThanOrEqual(Math.round(360 * SERIES_CHART_MIN_PLOT_FRACTION));
    expect(layout.plotH).toBeGreaterThanOrEqual(Math.round(200 * SERIES_CHART_MIN_PLOT_FRACTION));
    expect(layout.plotH).toBeGreaterThanOrEqual(SERIES_CHART_MIN_PLOT_PX);
    const yTop = layout.toY(layout.axisMax);
    const yBot = layout.toY(layout.axisMin);
    expect(yTop).toBeGreaterThanOrEqual(layout.margin.top);
    expect(yBot).toBeLessThanOrEqual(layout.margin.top + layout.plotH);
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

    expect(snapshot.x0).toBeCloseTo(snapshot.margin.left, 1);
    expect(snapshot.xLast).toBeCloseTo(snapshot.margin.left + snapshot.plotW, 1);
    expect(snapshot.firstAnchor).toBe("start");
    expect(snapshot.lastAnchor).toBe("end");
    expect(snapshot.plotInset).toBe(0);
    expect(snapshot.margin.right).toBeGreaterThanOrEqual(18);
    expect(snapshot.xLast - snapshot.x0).toBeGreaterThan(snapshot.plotW * 0.5);
  });

  it("toX(0)/toX(last) alinham às bordas do plot (sem gap do plotInset)", () => {
    const layout = buildSeriesChartLayout({
      points: [
        { label: "a", value: 10 },
        { label: "b", value: 20 },
        { label: "c", value: 30 },
      ],
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 240,
      categoryPaddingPercent: 0,
    });
    expect(layout.categoryScale).toBe("point");
    expect(layout.toX(0, 3)).toBeCloseTo(layout.margin.left, 5);
    expect(layout.toX(2, 3)).toBeCloseTo(layout.margin.left + layout.plotW, 5);
  });

  it("band: toX no centro da categoria (padrão Excel/ECharts/d3.scaleBand)", () => {
    const layout = buildSeriesChartLayout({
      points: Array.from({ length: 10 }, (_, i) => ({
        label: String(10020000 + i),
        value: 40 - i,
        sourceIndex: i,
      })),
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 240,
      categoryPaddingPercent: 0,
      categoryScale: "band",
    });
    expect(layout.categoryScale).toBe("band");
    const n = 10;
    for (let i = 0; i < n; i += 1) {
      const bandStart = layout.categoryBandStart(i, n);
      const bandW = layout.categoryBandWidth(n);
      expect(layout.toX(i, n)).toBeCloseTo(bandStart + bandW / 2, 5);
    }
    expect(resolveXLabelTextAnchor(0, n, false, "band")).toBe("middle");
    expect(resolveXLabelTextAnchor(n - 1, n, false, "band")).toBe("middle");
    expect(resolveSeriesChartCategoryScale("bar")).toBe("band");
    expect(resolveSeriesChartCategoryScale("line")).toBe("point");
  });

  it("band: centro da barra coincide com toX (rótulo do eixo)", () => {
    const points = Array.from({ length: 10 }, (_, i) => ({
      label: String(10020134 + i),
      value: 40 - i * 3,
      sourceIndex: i,
    }));
    const layout = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 640,
      viewH: 280,
      categoryPaddingPercent: 0,
      categoryScale: "band",
    });
    for (let i = 0; i < points.length; i += 1) {
      const slot = resolveSeriesChartCategoryBarSlot({
        layout,
        categoryIndex: i,
        categoryCount: points.length,
      });
      expect(slot.centerX).toBeCloseTo(layout.toX(i, points.length), 5);
    }
  });

  it("toY(axisMin) alinha ao eixo X (sem gap do plotInset vertical)", () => {
    const layout = buildSeriesChartLayout({
      points: [
        { label: "a", value: 0 },
        { label: "b", value: 100 },
      ],
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 240,
    });
    expect(layout.toY(layout.axisMin)).toBeCloseTo(layout.margin.top + layout.plotH, 5);
    expect(layout.toY(layout.axisMax)).toBeCloseTo(layout.margin.top, 5);
  });

  it("axisMax cobre dataMax para não clipar série no teto (economia vs investimento)", () => {
    const layout = buildSeriesChartLayout({
      points: [
        { label: "01", value: 120 },
        { label: "15", value: 875 },
        { label: "27", value: 890 },
      ],
      axisValues: [120, 200, 875, 890, 150],
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 240,
    });
    expect(layout.axisMax).toBeGreaterThanOrEqual(890);
    // Variação acima de 800 (antigo teto clipado) continua distinguível no plot
    expect(layout.toY(800)).toBeGreaterThan(layout.toY(875));
    expect(layout.toY(875)).toBeGreaterThan(layout.toY(890));
  });
});

describe("buildSeriesChartLayout secondary axis", () => {
  it("reserva eixo direito e toYSecondary quando há secondaryAxisValues", () => {
    const layout = buildSeriesChartLayout({
      points: [
        { label: "a", value: 10 },
        { label: "b", value: 20 },
      ],
      axisValues: [10, 20],
      secondaryAxisValues: [100, 200],
      showXAxisLabels: true,
      showXAxisTitle: false,
      viewW: 400,
      viewH: 240,
    });
    expect(layout.hasSecondaryAxis).toBe(true);
    expect(layout.toYSecondary).toBeTypeOf("function");
    expect(layout.secondaryTicks?.length).toBeGreaterThan(0);
    expect(layout.margin.right).toBeGreaterThan(20);
    const yPrimary = layout.toY(20);
    const ySecondary = layout.toYSecondary!(200);
    expect(yPrimary).toBeTypeOf("number");
    expect(ySecondary).toBeTypeOf("number");
  });
});

describe("category label rotation + horizontal_bar", () => {
  it("categoryLabelRotation -90 força rótulos verticais", () => {
    const labels = Array.from({ length: 12 }, (_, i) => `cat-${i}`);
    const layout = buildSeriesChartLayout({
      points: labels.map((label) => ({ label, value: 10 })),
      showXAxisLabels: true,
      showXAxisTitle: false,
      categoryLabelRotation: -90,
    });
    expect(layout.categoryLabelRotationDeg).toBe(-90);
    expect(layout.xLabelsRotated).toBe(true);
  });

  it("orientation horizontal expõe toValueX e bandas Y", () => {
    const layout = buildSeriesChartLayout({
      points: [
        { label: "A", value: 10 },
        { label: "B", value: 20 },
      ],
      showXAxisLabels: true,
      showXAxisTitle: false,
      orientation: "horizontal",
      categoryScale: "band",
    });
    expect(layout.orientation).toBe("horizontal");
    expect(typeof layout.toValueX).toBe("function");
    expect(typeof layout.categoryBandStartY).toBe("function");
    expect(layout.toValueX!(20)).toBeGreaterThan(layout.toValueX!(10));
  });

  it("orientation horizontal: desligar showX mantém índices de categoria (eixo Y)", () => {
    const points = [
      { label: "A", value: 10 },
      { label: "B", value: 20 },
      { label: "C", value: 30 },
    ];
    const both = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showYAxisLabels: true,
      showXAxisTitle: false,
      orientation: "horizontal",
      categoryScale: "band",
    });
    const onlyY = buildSeriesChartLayout({
      points,
      showXAxisLabels: false,
      showYAxisLabels: true,
      showXAxisTitle: false,
      orientation: "horizontal",
      categoryScale: "band",
    });
    const onlyX = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showYAxisLabels: false,
      showXAxisTitle: false,
      orientation: "horizontal",
      categoryScale: "band",
    });
    expect(both.visibleXLabelIndices.length).toBe(3);
    expect(onlyY.visibleXLabelIndices.length).toBe(3);
    expect(onlyX.visibleXLabelIndices).toEqual([]);
  });

  it("horizontal_bar: fonte do eixo Y amplia margem esquerda sem sobrepor o plot", () => {
    const labels = ["10080059", "10500316", "10090045", "10200018", "10300112"];
    const points = labels.map((label, index) => ({ label, value: 40 - index }));
    const small = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showYAxisLabels: true,
      showXAxisTitle: false,
      orientation: "horizontal",
      categoryScale: "band",
      viewW: 420,
      viewH: 280,
      typography: { axisFontSize: 14 },
    });
    const large = buildSeriesChartLayout({
      points,
      showXAxisLabels: true,
      showYAxisLabels: true,
      showXAxisTitle: false,
      orientation: "horizontal",
      categoryScale: "band",
      viewW: 420,
      viewH: 280,
      typography: { axisFontSize: 32 },
    });
    const needLarge = resolveHorizontalCategoryLabelLeftPad(labels, 32);
    expect(large.margin.left).toBeGreaterThan(small.margin.left);
    expect(large.margin.left).toBeGreaterThanOrEqual(needLarge);
    expect(large.plotW).toBeGreaterThanOrEqual(Math.round(420 * SERIES_CHART_MIN_PLOT_FRACTION));
  });

  it("horizontal_bar: plotFrame apertado ainda respeita gutter das categorias", () => {
    const labels = ["10080059", "10500316"];
    const layout = buildSeriesChartLayout({
      points: labels.map((label, index) => ({ label, value: 10 + index })),
      showXAxisLabels: true,
      showYAxisLabels: true,
      showXAxisTitle: false,
      orientation: "horizontal",
      categoryScale: "band",
      viewW: 420,
      viewH: 280,
      plotFrame: { x: 4, y: 8, w: 90, h: 80 },
      typography: { axisFontSize: 28 },
    });
    expect(layout.margin.left).toBeGreaterThanOrEqual(
      resolveHorizontalCategoryLabelLeftPad(labels, 28),
    );
  });
});
