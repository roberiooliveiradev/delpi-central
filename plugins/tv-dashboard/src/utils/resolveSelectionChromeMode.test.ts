import { describe, expect, it } from "vitest";

import {
  chartPartSelectionLabel,
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "./resolveSelectionChromeMode";

describe("resolveSelectionChromeMode", () => {
  it("bloco sem parte → mode block", () => {
    const mode = resolveSelectionChromeMode({
      selected: { id: "c1", type: "chart_view", frame: { x: 0, y: 0, w: 40, h: 40 }, chartType: "line" } as never,
    });
    expect(mode).toEqual({ mode: "block" });
  });

  it("parte de gráfico → part chrome (não misturar com layout global)", () => {
    const mode = resolveSelectionChromeMode({
      selected: { id: "c1", type: "chart_view", frame: { x: 0, y: 0, w: 40, h: 40 }, chartType: "area" } as never,
      selectedChartPart: { kind: "axisTitle", axis: "y" },
    });
    expect(isPartSelectionChrome(mode)).toBe(true);
    if (mode.mode === "part") {
      expect(mode.source).toBe("chart");
      expect(mode.partLabel).toBe("Título eixo Y");
      expect(mode.backLabel).toBe("Voltar ao gráfico");
    }
  });

  it("parte de KPI → part chrome", () => {
    const mode = resolveSelectionChromeMode({
      selected: { id: "k1", type: "kpi_view", frame: { x: 0, y: 0, w: 20, h: 20 } } as never,
      selectedKpiPart: { kind: "value" },
    });
    expect(isPartSelectionChrome(mode)).toBe(true);
    if (mode.mode === "part") {
      expect(mode.source).toBe("kpi");
      expect(mode.partLabel).toBe("Valor");
    }
  });

  it("parte de tabela → part chrome", () => {
    const mode = resolveSelectionChromeMode({
      selected: { id: "t1", type: "table_view", frame: { x: 0, y: 0, w: 40, h: 40 } } as never,
      selectedTablePart: { kind: "header" },
    });
    expect(isPartSelectionChrome(mode)).toBe(true);
    if (mode.mode === "part") {
      expect(mode.source).toBe("table");
      expect(mode.partLabel).toBe("Cabeçalho");
    }
  });

  it("chartPartSelectionLabel cobre grade e plot", () => {
    expect(chartPartSelectionLabel({ kind: "grid" })).toBe("Grade");
    expect(chartPartSelectionLabel({ kind: "plotArea" })).toBe("Área de plotagem");
    expect(chartPartSelectionLabel({ kind: "dataLabels" })).toBe("Rótulos de dados");
  });
});
