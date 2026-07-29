import { describe, expect, it } from "vitest";

import { resolveTableSelectionPanelTab } from "./resolveTableSelectionPanelTab";

describe("resolveTableSelectionPanelTab", () => {
  it("mantém pedidos explícitos de Design/Layout/Dados", () => {
    expect(
      resolveTableSelectionPanelTab({
        requested: "tableDesign",
        selectedBlockType: "table_view",
      }),
    ).toBe("tableDesign");
    expect(
      resolveTableSelectionPanelTab({
        requested: "tableLayout",
        selectedBlockType: "table_view",
      }),
    ).toBe("tableLayout");
    expect(
      resolveTableSelectionPanelTab({
        requested: "data",
        selectedBlockType: "table_view",
      }),
    ).toBe("data");
  });

  it("mapeia element→tableDesign quando a seleção é tabela", () => {
    expect(
      resolveTableSelectionPanelTab({
        requested: "element",
        selectedBlockType: "table_view",
        currentPanelTab: "layers",
      }),
    ).toBe("tableDesign");
  });

  it("preserva tableLayout se já estava em Layout ao pedir element", () => {
    expect(
      resolveTableSelectionPanelTab({
        requested: "element",
        selectedBlockType: "table_view",
        currentPanelTab: "tableLayout",
      }),
    ).toBe("tableLayout");
  });

  it("não altera element para blocos que não são tabela", () => {
    expect(
      resolveTableSelectionPanelTab({
        requested: "element",
        selectedBlockType: "shape",
      }),
    ).toBe("element");
    expect(
      resolveTableSelectionPanelTab({
        requested: "element",
        selectedBlockType: "chart_view",
      }),
    ).toBe("element");
  });

  it("normaliza pedidos legados (table/format) para element e remapeia tabela", () => {
    expect(
      resolveTableSelectionPanelTab({
        requested: "table",
        selectedBlockType: "table_view",
      }),
    ).toBe("tableDesign");
    expect(
      resolveTableSelectionPanelTab({
        requested: "format",
        selectedBlockType: "kpi_view",
      }),
    ).toBe("element");
  });
});
