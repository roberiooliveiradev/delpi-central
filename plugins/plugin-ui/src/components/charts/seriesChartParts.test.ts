import { describe, expect, it } from "vitest";

import { DEFAULT_SERIES_CHART_OPTIONS, mergeSeriesChartOptions } from "./seriesChartOptions";
import {
  chartOptionsToParts,
  findChartPartFromTarget,
  isChartPartRefEqual,
  mergeSeriesChartOptionsWithParts,
  parseChartPartRef,
  partsToChartOptions,
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

  it("findChartPartFromTarget lê data-chart-part", () => {
    const root = document.createElement("div");
    const child = document.createElement("span");
    child.setAttribute("data-chart-part", "legend");
    root.appendChild(child);
    expect(findChartPartFromTarget(child)).toEqual({ kind: "legend" });
    expect(isChartPartRefEqual({ kind: "legend" }, { kind: "legend" })).toBe(true);
  });
});
