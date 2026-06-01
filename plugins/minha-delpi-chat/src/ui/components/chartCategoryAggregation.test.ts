import { describe, expect, it } from "vitest";
import { aggregateChartRowsByCategory } from "./chartCategoryAggregation";

describe("aggregateChartRowsByCategory", () => {
  it("aggregates duplicate filial values", () => {
    const rows = [
      { filial: "01", eficiencia_percentual: 100, tempo_real_horas: 1 },
      { filial: "01", eficiencia_percentual: 200, tempo_real_horas: 3 },
      { filial: "02", eficiencia_percentual: 50, tempo_real_horas: 2 },
    ];

    const aggregated = aggregateChartRowsByCategory(rows, "filial", [
      "eficiencia_percentual",
    ]);

    expect(aggregated).toHaveLength(2);
    expect(aggregated.find((row) => row.filial === "01")?.eficiencia_percentual).toBe(
      175,
    );
  });
});
