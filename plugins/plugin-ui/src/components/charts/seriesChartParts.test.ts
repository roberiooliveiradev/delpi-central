import { describe, expect, it } from "vitest";

import { DECK_CHART_DEFAULTS } from "../../theme/deckColorCatalog";
import { DEFAULT_SERIES_CHART_OPTIONS, mergeSeriesChartOptions } from "./seriesChartOptions";
import {
  applyMarkerStyleToAll,
  chartOptionsToParts,
  chartPartAllowsEdit,
  chartPartAllowsFrame,
  chartPartAllowsMove,
  chartPartAllowsResize,
  chartPartCapabilities,
  chartPartTypographyStyle,
  defaultChartPartFrame,
  deleteChartPart,
  filterVisibleSeriesPoints,
  findChartPartFromTarget,
  isChartPartInteractionSelected,
  isChartPartRefEqual,
  isFullBleedChartAreaFrame,
  resolveChartPartFrameRoot,
  mergeChartPartsWithOptions,
  mergeSeriesChartOptionsWithParts,
  normalizeChartPartsForLoad,
  nudgeChartPartFrame,
  parseChartPartRef,
  partsToChartOptions,
  resizeChartPartFrame,
  resolveChartAreaStyle,
  resolveChartLinePartStroke,
  resolveChartPartFontSize,
  resolveMarkerStyle,
  resolveSeriesStrokeColor,
  serializeChartPartRef,
  upsertChartPartState,
} from "./seriesChartParts";

describe("seriesChartParts", () => {
  it("serializa e parseia refs estáveis", () => {
    expect(serializeChartPartRef({ kind: "title" })).toBe("title");
    expect(serializeChartPartRef({ kind: "series", seriesIndex: 0 })).toBe("series:0");
    expect(serializeChartPartRef({ kind: "marker", seriesIndex: 0, pointIndex: 3 })).toBe("marker:0:3");
    expect(serializeChartPartRef({ kind: "axes" })).toBe("axes");
    expect(parseChartPartRef("axes")).toEqual({ kind: "axes" });
    expect(parseChartPartRef("axisTitle:y")).toEqual({ kind: "axisTitle", axis: "y" });
    expect(parseChartPartRef("nope")).toBeNull();
  });

  it("round-trip options → parts → options preserva título e cor", () => {
    const options = mergeSeriesChartOptions({
      title: "OEE",
      seriesColor: "#112233",
      showDataTable: true,
      showMarkers: true,
    });
    const parts = chartOptionsToParts(options);
    const back = mergeSeriesChartOptions({
      ...DEFAULT_SERIES_CHART_OPTIONS,
      ...partsToChartOptions(parts),
    });
    expect(back.title).toBe("OEE");
    expect(back.seriesColor).toBe("#112233");
    expect(back.showDataTable).toBe(true);
  });

  it("mergeSeriesChartOptionsWithParts aplica override de parte", () => {
    const parts = upsertChartPartState({}, { kind: "title" }, { content: "Novo título", visible: true });
    const merged = mergeSeriesChartOptionsWithParts({ title: "Antigo" }, parts);
    expect(merged.title).toBe("Novo título");
  });

  it("resolve cor e marcador a partir de primitivos (stroke/fill)", () => {
    const parts = upsertChartPartState(
      upsertChartPartState({}, { kind: "series", seriesIndex: 0 }, { style: { stroke: "#abcdef" } }),
      { kind: "marker", seriesIndex: 0, pointIndex: 1 },
      { style: { fill: "#ff0000", markerRadius: 4 } },
    );
    const options = mergeSeriesChartOptions({ seriesColor: "#000000" });
    expect(resolveSeriesStrokeColor(options, parts)).toBe("#abcdef");
    expect(resolveMarkerStyle(parts, 0, 1, "#abcdef")).toEqual({
      fill: "#ff0000",
      stroke: undefined,
      strokeWidth: 0,
      radius: 4,
      visible: true,
    });
  });

  it("série herda stroke como primitivo line; marcador herda fill da série", () => {
    const parts = upsertChartPartState({}, { kind: "series", seriesIndex: 0 }, {
      style: { stroke: "#0d7a8c", strokeWidth: 3 },
    });
    const options = mergeSeriesChartOptions({});
    expect(resolveSeriesStrokeColor(options, parts)).toBe("#0d7a8c");
    expect(resolveMarkerStyle(parts, 0, 0, "#000").fill).toBe("#0d7a8c");
  });

  it("deleteChartPart oculta marcador sem apagar options da série", () => {
    const options = mergeSeriesChartOptions({ title: "ROL", seriesColor: "#123456" });
    const parts = chartOptionsToParts(options);
    const result = deleteChartPart(parts, { kind: "marker", seriesIndex: 0, pointIndex: 2 }, options);
    expect(result.parts["marker:0:2"]?.visible).toBe(false);
    expect(result.options.title).toBe("ROL");
    expect(result.options.seriesColor).toBe("#123456");
  });

  it("deleteChartPart oculta título via options flat", () => {
    const options = mergeSeriesChartOptions({ title: "OEE", showTitle: true });
    const result = deleteChartPart(chartOptionsToParts(options), { kind: "title" }, options);
    expect(result.parts.title?.visible).toBe(false);
    expect(result.options.showTitle).toBe(false);
  });

  it("applyMarkerStyleToAll replica estilo em todos os pontos", () => {
    const next = applyMarkerStyleToAll({}, 3, 0, { fill: "#ff00aa", markerRadius: 5 });
    expect(next["marker:0:0"]?.style?.fill).toBe("#ff00aa");
    expect(next["marker:0:1"]?.style?.markerRadius).toBe(5);
    expect(next["marker:0:2"]?.style?.fill).toBe("#ff00aa");
  });

  it("filterVisibleSeriesPoints remove pontos ocultos preservando sourceIndex", () => {
    const parts = upsertChartPartState({}, { kind: "marker", seriesIndex: 0, pointIndex: 1 }, {
      visible: false,
    });
    const filtered = filterVisibleSeriesPoints(
      [{ value: 1 }, { value: 2 }, { value: 3 }],
      parts,
      0,
    );
    expect(filtered.map((p) => p.sourceIndex)).toEqual([0, 2]);
  });

  it("nudgeChartPartFrame move título com clamp", () => {
    const nudged = nudgeChartPartFrame(
      upsertChartPartState({}, { kind: "title" }, { frame: { x: 10, y: 10 } }),
      { kind: "title" },
      5,
      -3,
    );
    expect(nudged.title?.frame).toEqual({ x: 15, y: 7, w: undefined, h: undefined });
  });

  it("mergeSeriesChartOptionsWithParts não deixa seed legado de axisTitle apagar show ligado", () => {
    const merged = mergeSeriesChartOptionsWithParts(
      { showXAxisTitle: true, showYAxisTitle: true, xAxisTitle: "Período", yAxisTitle: "OEE" },
      {
        "axisTitle:x": { visible: false },
        "axisTitle:y": { visible: false },
      },
    );
    expect(merged.showXAxisTitle).toBe(true);
    expect(merged.showYAxisTitle).toBe(true);
    expect(merged.xAxisTitle).toBe("Período");
  });

  it("defaults Delpi: série accent e chartArea com raio/sombra", () => {
    const parts = chartOptionsToParts(mergeSeriesChartOptions({}));
    expect(parts.chartArea?.style?.borderRadius).toBe(DECK_CHART_DEFAULTS.borderRadius);
    expect(parts.chartArea?.style?.boxShadow).toBe(DECK_CHART_DEFAULTS.boxShadow);
    expect(parts.plotArea?.style?.stroke).toBeTruthy();
    const options = mergeSeriesChartOptions({});
    expect(options.seriesColor).toBe("#089bdb");
    expect(resolveChartAreaStyle(options, parts).borderRadius).toBe(DECK_CHART_DEFAULTS.borderRadius);
    expect(resolveChartAreaStyle(options, parts).boxShadow).toBe(DECK_CHART_DEFAULTS.boxShadow);
  });

  it("resolveChartAreaStyle respeita borderRadius 0 (cantos retos)", () => {
    const options = mergeSeriesChartOptions({});
    const parts = upsertChartPartState(chartOptionsToParts(options), { kind: "chartArea" }, {
      style: { borderRadius: 0, boxShadow: "none" },
    });
    expect(resolveChartAreaStyle(options, parts).borderRadius).toBe(0);
  });

  it("mergeChartPartsWithOptions aplica seriesColor novo sobre stroke da série", () => {
    const base = chartOptionsToParts(mergeSeriesChartOptions({ seriesColor: "#089bdb" }));
    const customized = upsertChartPartState(base, { kind: "series", seriesIndex: 0 }, {
      style: { stroke: "#089bdb", fill: "#089bdb", strokeWidth: 3 },
    });
    const merged = mergeChartPartsWithOptions(
      customized,
      mergeSeriesChartOptions({ seriesColor: "#0f766e" }),
    );
    expect(merged["series:0"]?.style?.stroke).toBe("#0f766e");
    expect(merged["series:0"]?.style?.fill).toBe("#0f766e");
    expect(merged["series:0"]?.style?.strokeWidth).toBe(3);
  });

  it("partsToChartOptions não força theme light (permite estilo Escuro)", () => {
    const options = mergeSeriesChartOptions({
      theme: "dark",
      backgroundColor: "#0b1520",
    });
    const parts = mergeChartPartsWithOptions(null, options);
    const fromParts = partsToChartOptions(parts);
    expect(fromParts.theme).toBeUndefined();
    expect(fromParts.backgroundColor).toBe("#0b1520");
    const effective = mergeSeriesChartOptionsWithParts(options, parts);
    expect(effective.theme).toBe("dark");
    expect(effective.backgroundColor).toBe("#0b1520");
  });

  it("mergeChartPartsWithOptions aplica categoryColors[1] no fill da série", () => {
    const merged = mergeChartPartsWithOptions(
      chartOptionsToParts(mergeSeriesChartOptions({ seriesColor: "#0f766e" })),
      mergeSeriesChartOptions({
        seriesColor: "#0f766e",
        categoryColors: ["#0f766e", "#14b8a6", "#115e59"],
      }),
    );
    expect(merged["series:0"]?.style?.stroke).toBe("#0f766e");
    expect(merged["series:0"]?.style?.fill).toBe("#14b8a6");
  });

  it("mergeChartPartsWithOptions aplica showMarkers sobre marker parts", () => {
    const withHidden = {
      ...chartOptionsToParts(mergeSeriesChartOptions({ showMarkers: false })),
      "marker:0:0": { visible: false },
    };
    const shown = mergeChartPartsWithOptions(
      withHidden,
      mergeSeriesChartOptions({ showMarkers: true }),
    );
    expect(shown["marker:0:0"]?.visible).toBe(true);
  });

  it("mergeChartPartsWithOptions preserva borda custom da chartArea", () => {
    const base = chartOptionsToParts(mergeSeriesChartOptions({}));
    const customized = upsertChartPartState(base, { kind: "chartArea" }, {
      style: { stroke: "#ff0000", strokeWidth: 3 },
    });
    const merged = mergeChartPartsWithOptions(
      customized,
      mergeSeriesChartOptions({ title: "X", backgroundColor: "#ffffff" }),
    );
    expect(merged.chartArea?.style?.stroke).toBe("#ff0000");
    expect(merged.chartArea?.style?.strokeWidth).toBe(3);
    expect(merged.chartArea?.style?.fill).toBe("#ffffff");
  });

  it("capabilities declarativas: title e plotArea móveis/redimensionáveis; plotArea não deletável", () => {
    expect(chartPartCapabilities({ kind: "title" })).toEqual({
      movable: true,
      editable: true,
      deletable: true,
      resizable: true,
    });
    expect(chartPartAllowsMove({ kind: "title" })).toBe(true);
    expect(chartPartAllowsEdit({ kind: "dataLabel", seriesIndex: 0, pointIndex: 0 })).toBe(true);
    expect(chartPartAllowsMove({ kind: "plotArea" })).toBe(true);
    expect(chartPartAllowsResize({ kind: "plotArea" })).toBe(true);
    expect(chartPartCapabilities({ kind: "plotArea" }).deletable).toBe(false);
    expect(chartPartCapabilities({ kind: "axis", axis: "x" }).resizable).toBe(false);
    expect(chartPartCapabilities({ kind: "legend" }).resizable).toBe(true);
  });

  it("chartPartAllowsFrame cobre title/legend/plotArea/chartArea", () => {
    expect(chartPartAllowsFrame({ kind: "title" })).toBe(true);
    expect(chartPartAllowsFrame({ kind: "legend" })).toBe(true);
    expect(chartPartAllowsFrame({ kind: "plotArea" })).toBe(true);
    expect(chartPartAllowsFrame({ kind: "chartArea" })).toBe(true);
    expect(chartPartAllowsFrame({ kind: "series", seriesIndex: 0 })).toBe(false);
    expect(chartPartAllowsFrame({ kind: "dataLabels" })).toBe(false);
    expect(chartPartAllowsFrame({ kind: "axes" })).toBe(false);
    expect(chartPartAllowsFrame({ kind: "grid" })).toBe(false);
    expect(chartPartAllowsFrame({ kind: "dataLabel", seriesIndex: 0, pointIndex: 0 })).toBe(false);
  });

  it("defaultChartPartFrame entrega % estáveis", () => {
    expect(defaultChartPartFrame({ kind: "title" }).w).toBe(80);
    expect(defaultChartPartFrame({ kind: "plotArea" }).h).toBe(84);
    expect(defaultChartPartFrame({ kind: "legend" }).y).toBe(85);
  });

  it("isFullBleedChartAreaFrame trata null e ≈100% como fluído", () => {
    expect(isFullBleedChartAreaFrame(null)).toBe(true);
    expect(isFullBleedChartAreaFrame(undefined)).toBe(true);
    expect(isFullBleedChartAreaFrame({ x: 0, y: 0, w: 100, h: 100 })).toBe(true);
    expect(isFullBleedChartAreaFrame({ x: 0, y: 0, w: 99.5, h: 99.5 })).toBe(true);
    expect(isFullBleedChartAreaFrame({ x: 5, y: 5, w: 80, h: 80 })).toBe(false);
  });

  it("resolveChartPartFrameRoot prioriza shell para chartArea", () => {
    const shell = document.createElement("div");
    shell.className = "delpi-ui-series-chart-shell";
    const chart = document.createElement("div");
    chart.className = "delpi-ui-series-chart";
    shell.appendChild(chart);
    document.body.appendChild(shell);
    expect(resolveChartPartFrameRoot({ kind: "chartArea" }, chart)).toBe(shell);
    shell.remove();
  });

  it("resizeChartPartFrame ajusta se e nw com clamp", () => {
    const se = resizeChartPartFrame({ x: 10, y: 10, w: 20, h: 10 }, "se", 5, 4);
    expect(se.w).toBe(25);
    expect(se.h).toBe(14);
    const nw = resizeChartPartFrame({ x: 20, y: 20, w: 30, h: 20 }, "nw", 5, 5);
    expect(nw.x).toBe(25);
    expect(nw.y).toBe(25);
    expect(nw.w).toBe(25);
    expect(nw.h).toBe(15);
  });

  it("normalizeChartPartsForLoad zera strokeWidth legado 1 do plotArea", () => {
    const legacy = upsertChartPartState(chartOptionsToParts(mergeSeriesChartOptions({})), {
      kind: "plotArea",
    }, { style: { strokeWidth: 1, stroke: "#b4b4b4" } });
    expect(legacy.plotArea?.style?.strokeWidth).toBe(1);
    const normalized = normalizeChartPartsForLoad(legacy, mergeSeriesChartOptions({}));
    expect(normalized.plotArea?.style?.strokeWidth).toBe(0);
  });

  it("normalizeChartPartsForLoad preserva strokeWidth explícito > 1", () => {
    const custom = upsertChartPartState(chartOptionsToParts(mergeSeriesChartOptions({})), {
      kind: "plotArea",
    }, { style: { strokeWidth: 2, stroke: "#333333" } });
    const normalized = normalizeChartPartsForLoad(custom, mergeSeriesChartOptions({}));
    expect(normalized.plotArea?.style?.strokeWidth).toBe(2);
  });

  it("normalizeChartPartsForLoad remove frame da dataTable e plotArea inválido", () => {
    const withFrames = {
      ...chartOptionsToParts(mergeSeriesChartOptions({ showDataTable: true })),
      dataTable: { visible: true, frame: { x: 0, y: 10, w: 40, h: 50 } },
      plotArea: { visible: true, frame: { x: 0, y: 0, w: 2, h: 2 } },
    };
    const normalized = normalizeChartPartsForLoad(withFrames, mergeSeriesChartOptions({ showDataTable: true }));
    expect(normalized.dataTable?.frame).toBeUndefined();
    expect(normalized.plotArea?.frame).toBeUndefined();
  });

  it("isChartPartInteractionSelected destaca todos os rótulos no grupo dataLabels", () => {
    expect(
      isChartPartInteractionSelected(
        { kind: "dataLabel", seriesIndex: 0, pointIndex: 2 },
        { kind: "dataLabels" },
      ),
    ).toBe(true);
    expect(
      isChartPartInteractionSelected(
        { kind: "dataLabel", seriesIndex: 0, pointIndex: 2 },
        { kind: "dataLabel", seriesIndex: 0, pointIndex: 1 },
      ),
    ).toBe(false);
  });

  it("isChartPartInteractionSelected destaca ambos os eixos no grupo axes", () => {
    expect(
      isChartPartInteractionSelected({ kind: "axis", axis: "x" }, { kind: "axes" }),
    ).toBe(true);
    expect(
      isChartPartInteractionSelected({ kind: "axis", axis: "y" }, { kind: "axes" }),
    ).toBe(true);
    expect(
      isChartPartInteractionSelected({ kind: "axis", axis: "x" }, { kind: "axis", axis: "y" }),
    ).toBe(false);
  });

  it("partsToChartOptions não força grade vertical quando a parte grid está ligada", () => {
    const parts = chartOptionsToParts(
      mergeSeriesChartOptions({ showGrid: true, showVerticalGrid: false }),
    );
    expect(parts.grid?.visible).toBe(true);
    const fromParts = partsToChartOptions(parts);
    expect(fromParts.showGrid).toBeUndefined();
    expect(fromParts.showVerticalGrid).toBeUndefined();
    const merged = mergeSeriesChartOptionsWithParts(
      { showGrid: true, showVerticalGrid: false },
      parts,
    );
    expect(merged.showGrid).toBe(true);
    expect(merged.showVerticalGrid).toBe(false);
  });

  it("partsToChartOptions desliga H+V quando grid.visible=false", () => {
    const parts = upsertChartPartState({}, { kind: "grid" }, { visible: false });
    expect(partsToChartOptions(parts)).toMatchObject({
      showGrid: false,
      showVerticalGrid: false,
    });
  });

  it("resolveChartLinePartStroke herda estilo do grupo axes", () => {
    const parts = upsertChartPartState({}, { kind: "axes" }, {
      style: { stroke: "#ff0000", strokeWidth: 3 },
    });
    expect(resolveChartLinePartStroke(parts, { kind: "axis", axis: "x" })).toEqual({
      stroke: "#ff0000",
      strokeWidth: 3,
      opacity: undefined,
    });
  });

  it("chartPartTypographyStyle em título aplica caixa coluna (verticalAlign)", () => {
    const parts = upsertChartPartState({}, { kind: "title" }, {
      style: { fontSize: 18, textAlign: "center", verticalAlign: "bottom" },
    });
    expect(chartPartTypographyStyle(parts, { kind: "title" })).toMatchObject({
      fontSize: "18px",
      display: "flex",
      flexDirection: "column",
      justifyContent: "flex-end",
      alignItems: "center",
      textAlign: "center",
    });
  });

  it("resolveChartPartFontSize e tipografia usam defaults canônicos (não 16 fantasma)", () => {
    expect(resolveChartPartFontSize("axis")).toBe(14);
    expect(resolveChartPartFontSize("axisTitle")).toBe(14);
    expect(resolveChartPartFontSize("dataLabel")).toBe(12);
    expect(resolveChartPartFontSize("title")).toBe(22);
    expect(resolveChartPartFontSize("legend")).toBe(16);
    expect(resolveChartPartFontSize("axis", { fontSize: 16 })).toBe(16);
    expect(chartPartTypographyStyle({}, { kind: "axis", axis: "y" })).toEqual({ fontSize: "14px" });
    expect(chartPartTypographyStyle({}, { kind: "axis", axis: "x" })).toEqual({ fontSize: "14px" });
  });
});
