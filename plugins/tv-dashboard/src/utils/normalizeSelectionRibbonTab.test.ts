import { describe, expect, it } from "vitest";

import {
  isSelectionPanelTab,
  normalizeSelectionRibbonTab,
} from "./normalizeSelectionRibbonTab";

describe("normalizeSelectionRibbonTab", () => {
  it("mapeia Forma/Gráfico/Tabela/Formatar para Elemento", () => {
    expect(normalizeSelectionRibbonTab("shape")).toBe("element");
    expect(normalizeSelectionRibbonTab("chart")).toBe("element");
    expect(normalizeSelectionRibbonTab("table")).toBe("element");
    expect(normalizeSelectionRibbonTab("kpi")).toBe("element");
    expect(normalizeSelectionRibbonTab("canvasTable")).toBe("element");
    expect(normalizeSelectionRibbonTab("format")).toBe("element");
    expect(normalizeSelectionRibbonTab("element")).toBe("element");
  });

  it("preserva Dados, Camadas, Inserir e Exibir", () => {
    expect(normalizeSelectionRibbonTab("data")).toBe("data");
    expect(normalizeSelectionRibbonTab("layers")).toBe("layers");
    expect(normalizeSelectionRibbonTab("insert")).toBe("insert");
    expect(normalizeSelectionRibbonTab("view")).toBe("view");
  });

  it("reconhece abas do painel", () => {
    expect(isSelectionPanelTab("element")).toBe(true);
    expect(isSelectionPanelTab("tableDesign")).toBe(true);
    expect(isSelectionPanelTab("tableLayout")).toBe(true);
    expect(isSelectionPanelTab("insert")).toBe(false);
  });
});
