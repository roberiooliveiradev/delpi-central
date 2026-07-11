import { describe, expect, it } from "vitest";

import { DEFAULT_SERIES_CHART_OPTIONS, mergeSeriesChartOptions } from "./seriesChartOptions";
import {
  applyMarkerStyleToAll,
  chartOptionsToParts,
  deleteChartPart,
  filterVisibleSeriesPoints,
  findChartPartFromTarget,
  isChartPartRefEqual,
  mergeChartPartsWithOptions,
  mergeSeriesChartOptionsWithParts,
  nudgeChartPartFrame,
  parseChartPartRef,
  partsToChartOptions,
  resolveChartAreaStyle,
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

  it("defaults Office: série azul da forma e chartArea com cantos 0", () => {
    const parts = chartOptionsToParts(mergeSeriesChartOptions({}));
    expect(parts.chartArea?.style?.fill).toBe("#ffffff");
    expect(parts.chartArea?.style?.borderRadius).toBe(0);
    expect(parts.plotArea?.style?.stroke).toBeTruthy();
    const options = mergeSeriesChartOptions({});
    expect(options.seriesColor).toBe("#089bdb");
    expect(resolveChartAreaStyle(options, parts).borderRadius).toBe(0);
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
});
