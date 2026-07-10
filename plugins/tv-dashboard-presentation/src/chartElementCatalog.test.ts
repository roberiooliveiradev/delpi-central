import { describe, expect, it } from "vitest";

import {
  CHART_ELEMENT_CATALOG,
  isChartElementApplicable,
  isChartElementEnabled,
  setChartElementEnabled,
} from "./chartElementCatalog";
import { DEFAULT_COMUNICADO_CHART_OPTIONS, mergeComunicadoChartOptions } from "./comunicadoChartOptions";

describe("chartElementCatalog", () => {
  it("lista elementos no estilo Excel", () => {
    const labels = CHART_ELEMENT_CATALOG.map((entry) => entry.label);
    expect(labels).toContain("Eixos");
    expect(labels).toContain("Tabela de dados");
    expect(labels).toContain("Legenda");
  });

  it("marcadores só em gráfico de linhas", () => {
    const markers = CHART_ELEMENT_CATALOG.find((entry) => entry.id === "markers");
    expect(markers).toBeTruthy();
    expect(isChartElementApplicable(markers!, "line")).toBe(true);
    expect(isChartElementApplicable(markers!, "bar")).toBe(false);
  });

  it("ativa e desativa legenda", () => {
    const enabled = mergeComunicadoChartOptions(setChartElementEnabled("legend", true));
    expect(isChartElementEnabled("legend", enabled)).toBe(true);
    const disabled = mergeComunicadoChartOptions(setChartElementEnabled("legend", false));
    expect(isChartElementEnabled("legend", disabled)).toBe(false);
  });

  it("tabela de dados desligada por padrão", () => {
    expect(isChartElementEnabled("dataTable", DEFAULT_COMUNICADO_CHART_OPTIONS)).toBe(false);
    const on = mergeComunicadoChartOptions(setChartElementEnabled("dataTable", true));
    expect(isChartElementEnabled("dataTable", on)).toBe(true);
  });
});
