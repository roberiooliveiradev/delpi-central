import { describe, expect, it } from "vitest";

import {
  formatPanelTabForBlockType,
  resolveFormatSelectionPanelTab,
} from "./resolveTableSelectionPanelTab";

describe("formatPanelTabForBlockType", () => {
  it("tabela → Design (ou Layout se já estava)", () => {
    expect(formatPanelTabForBlockType("table_view")).toBe("tableDesign");
    expect(formatPanelTabForBlockType("table_view", "tableLayout")).toBe("tableLayout");
  });

  it("gráfico/KPI/forma → Elemento", () => {
    expect(formatPanelTabForBlockType("chart_view")).toBe("element");
    expect(formatPanelTabForBlockType("kpi_view")).toBe("element");
    expect(formatPanelTabForBlockType("shape")).toBe("element");
  });

  it("fonte de dados → Dados", () => {
    expect(formatPanelTabForBlockType("data_source")).toBe("data");
  });
});

describe("resolveFormatSelectionPanelTab", () => {
  it("mapeia element→tableDesign quando a seleção é tabela", () => {
    expect(
      resolveFormatSelectionPanelTab({
        requested: "element",
        selectedBlockType: "table_view",
        currentPanelTab: "layers",
      }),
    ).toBe("tableDesign");
  });

  it("preserva tableLayout se já estava em Layout ao pedir element", () => {
    expect(
      resolveFormatSelectionPanelTab({
        requested: "element",
        selectedBlockType: "table_view",
        currentPanelTab: "tableLayout",
      }),
    ).toBe("tableLayout");
  });

  it("element em gráfico/KPI permanece element (não tableDesign)", () => {
    expect(
      resolveFormatSelectionPanelTab({
        requested: "element",
        selectedBlockType: "chart_view",
        currentPanelTab: "tableDesign",
      }),
    ).toBe("element");
    expect(
      resolveFormatSelectionPanelTab({
        requested: "shape",
        selectedBlockType: "chart_view",
      }),
    ).toBe("element");
    expect(
      resolveFormatSelectionPanelTab({
        requested: "chart",
        selectedBlockType: "kpi_view",
      }),
    ).toBe("element");
  });

  it("pedido tableDesign com bloco não-tabela remapeia para a aba do bloco", () => {
    expect(
      resolveFormatSelectionPanelTab({
        requested: "tableDesign",
        selectedBlockType: "chart_view",
      }),
    ).toBe("element");
  });

  it("mantém data/layers", () => {
    expect(
      resolveFormatSelectionPanelTab({
        requested: "data",
        selectedBlockType: "chart_view",
      }),
    ).toBe("data");
    expect(
      resolveFormatSelectionPanelTab({
        requested: "layers",
        selectedBlockType: "table_view",
      }),
    ).toBe("layers");
  });
});
