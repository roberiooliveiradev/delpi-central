import { describe, expect, it } from "vitest";

import { buildAnnualComparisonChartModel } from "./ConsumptionAnnualComparisonChart";

describe("buildAnnualComparisonChartModel", () => {
  it("pivota valores por ano no eixo Jan–Dez", () => {
    const model = buildAnnualComparisonChartModel({
      years: ["2024", "2025", "2026"],
      items: [
        {
          month: 1,
          month_label: "Jan",
          values_by_year: { "2024": 10, "2025": 20, "2026": 0 },
        },
        {
          month: 2,
          month_label: "Fev",
          values_by_year: { "2024": 5, "2025": null, "2026": null },
        },
      ],
      total: 2,
      period_start: "2024-01-01",
      period_end: "2026-07-17",
    });

    expect(model.series.map((item) => item.key)).toEqual(["2024", "2025", "2026"]);
    expect(model.points[0]).toEqual({
      label: "Jan",
      "2024": 10,
      "2025": 20,
      "2026": 0,
    });
    expect(model.points[1]?.["2025"]).toBeNull();
  });
});
