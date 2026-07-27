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
  it("hints do catálogo em português (sem jargão Office em inglês)", () => {
    for (const entry of SERIES_CHART_ELEMENT_CATALOG) {
      expect(entry.hint ?? "").not.toMatch(/Format Chart|Format Plot|Office/i);
    }
  });

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
      { kind: "axes" },
      { kind: "axis", axis: "x" },
      { kind: "axis", axis: "y" },
    ]);
    expect(chartElementPrimaryPartRef("axes")).toEqual({ kind: "axes" });
    expect(chartElementPrimaryPartRef("dataLabels")).toEqual({
      kind: "dataLabels",
    });
    expect(chartElementIdForPartRef({ kind: "axes" })).toBe("axes");
    expect(isChartElementOpenForPart("axes", { kind: "axes" })).toBe(true);
    expect(chartElementPrimaryPartRef("markers")).toEqual({
      kind: "marker",
      seriesIndex: 0,
      pointIndex: 0,
    });
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

  it("desligar/ligar legenda preserva posição e não usa hidden", () => {
    const base = mergeSeriesChartOptions({
      showLegend: true,
      legendPosition: "left",
      seriesName: "LMP",
    });
    const off = applyChartElementVisibility("legend", false, base, {
      legend: { visible: true, content: "LMP", style: { fill: "#eee" } },
    });
    expect(off.options.showLegend).toBe(false);
    expect(off.options.legendPosition).toBe("left");
    expect(off.parts.legend?.content).toBe("LMP");
    expect(off.parts.legend?.style?.fill).toBe("#eee");

    const on = applyChartElementVisibility("legend", true, off.options, off.parts);
    expect(on.options.showLegend).toBe(true);
    expect(on.options.legendPosition).toBe("left");
    expect(on.parts.legend?.content).toBe("LMP");
    expect(on.parts.legend?.style?.fill).toBe("#eee");
  });

  it("desligar/ligar rótulos preserva dataLabels custom", () => {
    const base = mergeSeriesChartOptions({
      showDataLabels: true,
      dataLabels: {
        showCategoryName: true,
        showPercentage: true,
        showValue: false,
        position: "outsideEnd",
        showLeaderLines: true,
      },
    });
    const off = applyChartElementVisibility("dataLabels", false, base, null);
    expect(off.options.showDataLabels).toBe(false);
    expect(off.options.dataLabels).toMatchObject({
      showCategoryName: true,
      showPercentage: true,
      position: "outsideEnd",
    });
    const on = applyChartElementVisibility("dataLabels", true, off.options, off.parts);
    expect(on.options.showDataLabels).toBe(true);
    expect(on.options.dataLabels?.position).toBe("outsideEnd");
  });

  it("gridlines liga só horizontal sem forçar vertical no catálogo", () => {
    const off = mergeSeriesChartOptions(setSeriesChartElementEnabled("gridlines", false));
    expect(off.showGrid).toBe(false);
    expect(off.showVerticalGrid).toBe(false);
    const on = mergeSeriesChartOptions({
      ...off,
      ...setSeriesChartElementEnabled("gridlines", true),
    });
    expect(on.showGrid).toBe(true);
    expect(on.showVerticalGrid).toBe(false);
  });
});
