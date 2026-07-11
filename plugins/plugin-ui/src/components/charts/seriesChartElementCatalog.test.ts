import { describe, expect, it } from "vitest";

import {
  SERIES_CHART_ELEMENT_CATALOG,
  applyChartElementVisibility,
  chartElementIdForPartRef,
  chartElementPartRefs,
  chartElementPrimaryPartRef,
  isChartElementOpenForPart,
  isSeriesChartElementApplicable,
  isSeriesChartElementEnabled,
  setSeriesChartElementEnabled,
} from "./seriesChartElementCatalog";
import { DEFAULT_SERIES_CHART_OPTIONS, mergeSeriesChartOptions } from "./seriesChartOptions";

describe("seriesChartElementCatalog", () => {
  it("lista elementos no estilo Excel", () => {
    const labels = SERIES_CHART_ELEMENT_CATALOG.map((entry) => entry.label);
    expect(labels).toContain("Eixos");
    expect(labels).toContain("Tabela de dados");
    expect(labels).toContain("Legenda");
    expect(labels).toContain("Série");
  });

  it("marcadores só em gráfico de linhas", () => {
    const markers = SERIES_CHART_ELEMENT_CATALOG.find((entry) => entry.id === "markers");
    expect(markers).toBeTruthy();
    expect(isSeriesChartElementApplicable(markers!, "line")).toBe(true);
    expect(isSeriesChartElementApplicable(markers!, "bar")).toBe(false);
  });

  it("ativa e desativa legenda", () => {
    const enabled = mergeSeriesChartOptions(setSeriesChartElementEnabled("legend", true));
    expect(isSeriesChartElementEnabled("legend", enabled)).toBe(true);
    const disabled = mergeSeriesChartOptions(setSeriesChartElementEnabled("legend", false));
    expect(isSeriesChartElementEnabled("legend", disabled)).toBe(false);
  });

  it("tabela de dados desligada por padrão", () => {
    expect(isSeriesChartElementEnabled("dataTable", DEFAULT_SERIES_CHART_OPTIONS)).toBe(false);
    const on = mergeSeriesChartOptions(setSeriesChartElementEnabled("dataTable", true));
    expect(isSeriesChartElementEnabled("dataTable", on)).toBe(true);
  });

  it("mapeia catálogo → ChartPartRef (4G.7)", () => {
    expect(chartElementPrimaryPartRef("chartTitle")).toEqual({ kind: "title" });
    expect(chartElementPartRefs("axes")).toEqual([
      { kind: "axis", axis: "x" },
      { kind: "axis", axis: "y" },
    ]);
    expect(chartElementIdForPartRef({ kind: "series", seriesIndex: 0 })).toBe("series");
    expect(isChartElementOpenForPart("legend", { kind: "legend" })).toBe(true);
  });

  it("applyChartElementVisibility sincroniza options e parts", () => {
    const base = mergeSeriesChartOptions({ showTitle: true, title: "OEE" });
    const off = applyChartElementVisibility("chartTitle", false, base, null);
    expect(off.options.showTitle).toBe(false);
    expect(off.parts.title?.visible).toBe(false);

    const on = applyChartElementVisibility("legend", false, base, off.parts);
    expect(on.options.showLegend).toBe(false);
    expect(on.parts.legend?.visible).toBe(false);
  });
});
