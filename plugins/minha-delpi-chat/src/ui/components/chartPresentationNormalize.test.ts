import { describe, expect, it } from "vitest";

import { normalizeChartPresentation } from "./chartPresentationNormalize";

describe("normalizeChartPresentation", () => {
  it("converte labels/datasets legados em data[]", () => {
    const chart = normalizeChartPresentation({
      type: "chart",
      chartType: "donut",
      title: "Composição por tipo de componente",
      labels: ["MP (7)", "PI (2)"],
      datasets: [{ label: "Itens", data: [7, 2] }],
    });

    expect(chart).not.toBeNull();
    expect(chart?.data).toEqual([
      { label: "MP (7)", value: 7 },
      { label: "PI (2)", value: 2 },
    ]);
    expect(chart?.config?.xAxis).toBe("label");
    expect(chart?.config?.yAxis).toBe("value");
  });

  it("preserva data[] quando já veio normalizado", () => {
    const chart = normalizeChartPresentation({
      type: "chart",
      chartType: "bar",
      title: "Faturamento",
      data: [{ filial: "01", total: 10 }],
    });

    expect(chart?.data).toEqual([{ filial: "01", total: 10 }]);
  });
});
