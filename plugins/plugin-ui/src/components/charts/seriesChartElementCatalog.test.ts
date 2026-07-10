import { describe, expect, it } from "vitest";

import {
  SERIES_CHART_ELEMENT_CATALOG,
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
});
