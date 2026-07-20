import { describe, expect, it } from "vitest";

import { buildConsumptionMonthlyChartData } from "./ConsumptionMonthlyAverageChart";

describe("buildConsumptionMonthlyChartData", () => {
  it("adiciona a média dos 12 meses a todos os pontos", () => {
    const result = buildConsumptionMonthlyChartData(
      [
        {
          year_month: "202601",
          year_month_label: "2026-01",
          consumption_quantity: 80,
          movement_count: 2,
        },
        {
          year_month: "202602",
          year_month_label: "2026-02",
          consumption_quantity: 120,
          movement_count: 3,
        },
      ],
      1200,
    );

    expect(result).toEqual([
      { period: "2026-01", consumption: 80, monthlyAverage: 100 },
      { period: "2026-02", consumption: 120, monthlyAverage: 100 },
    ]);
  });

  it("não produz média negativa", () => {
    const result = buildConsumptionMonthlyChartData(
      [
        {
          year_month: "202601",
          year_month_label: "2026-01",
          consumption_quantity: -10,
          movement_count: 1,
        },
      ],
      -10,
    );

    expect(result[0]?.monthlyAverage).toBe(0);
    expect(result[0]?.consumption).toBe(-10);
  });
});
