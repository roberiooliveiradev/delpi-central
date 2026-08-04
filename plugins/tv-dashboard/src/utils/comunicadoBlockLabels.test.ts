import { describe, expect, it } from "vitest";
import type { ComunicadoTextBlock } from "@delpi/tv-dashboard-presentation";

import { comunicadoBlockSummary, comunicadoBlockTypeLabel } from "./comunicadoBlockLabels";

describe("comunicadoBlockTypeLabel", () => {
  it("traduz chart_view, table_view e kpi_view para o gestor", () => {
    expect(comunicadoBlockTypeLabel("chart_view")).toBe("Gráfico");
    expect(comunicadoBlockTypeLabel("table_view")).toBe("Tabela");
    expect(comunicadoBlockTypeLabel("kpi_view")).toBe("KPI");
    expect(comunicadoBlockTypeLabel("data_source")).toBe("Fonte de dados");
  });
});

describe("comunicadoBlockSummary", () => {
  it("texto com binding usa valor projetado, não content estático", () => {
    const block: ComunicadoTextBlock = {
      id: "t1",
      type: "text",
      frame: { x: 0, y: 0, w: 20, h: 10 },
      content: "Realizado 0,74",
      dataSourceId: "src-1",
      textProjection: {
        field: "value",
        format: "number",
        decimalPlaces: 2,
        prefix: "Realizado ",
      },
      resolved: {
        kpi: { value: 0.55, label: "value" },
        kpiMetrics: [{ field: "value", value: 0.55, label: "value" }],
      },
      style: {},
    };
    expect(comunicadoBlockSummary(block)).toBe("Realizado 0,55");
  });
});
