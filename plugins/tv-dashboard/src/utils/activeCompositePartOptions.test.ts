import { describe, expect, it } from "vitest";

import {
  activePartOptionValue,
  listChartActivePartOptions,
  listKpiActivePartOptions,
  listTableActivePartOptions,
} from "./activeCompositePartOptions";

describe("activeCompositePartOptions", () => {
  it("lista séries do chartProjection no dropdown", () => {
    const options = listChartActivePartOptions({
      id: "c1",
      type: "chart_view",
      frame: { x: 0, y: 0, w: 40, h: 30 },
      chartProjection: {
        series: [
          { field: "oee", label: "OEE" },
          { field: "meta", label: "Meta" },
        ],
      },
    } as never);
    expect(options.some((item) => item.value === "series:0" && item.label.includes("OEE"))).toBe(
      true,
    );
    expect(options.some((item) => item.value === "series:1" && item.label.includes("Meta"))).toBe(
      true,
    );
  });

  it("lista métricas do KPI", () => {
    const options = listKpiActivePartOptions({
      id: "k1",
      type: "kpi_view",
      frame: { x: 0, y: 0, w: 20, h: 15 },
      kpiProjection: { metrics: [{ field: "oee", label: "OEE", visible: true }] },
    } as never);
    expect(options.some((item) => item.value === "metricCard:oee")).toBe(true);
  });

  it("lista colunas da tabela a partir da projeção", () => {
    const options = listTableActivePartOptions({
      id: "t1",
      type: "table_view",
      frame: { x: 0, y: 0, w: 40, h: 30 },
      tableProjection: {
        columns: [
          { key: "branch", label: "Filial", visible: true },
          { key: "hidden", label: "Oculta", visible: false },
        ],
      },
    } as never);
    expect(options.some((item) => item.value === "headerCell:0")).toBe(true);
    expect(options.some((item) => item.label.includes("Oculta"))).toBe(false);
  });

  it("serializa valor ativo da parte do gráfico", () => {
    expect(activePartOptionValue({ chartPart: { kind: "series", seriesIndex: 2 } })).toBe(
      "series:2",
    );
  });
});
