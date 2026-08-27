import { describe, expect, it } from "vitest";

import {
  chartAxesEditorHint,
  resolveChartDataPolicy,
  resolveChartSeriesDefaultAggregation,
} from "./chartDataPolicy";

describe("chartDataPolicy", () => {
  it("pizza/rosca usam groupByCategory com soma (medida); contagem só sem medida", () => {
    expect(resolveChartDataPolicy("pie").rowMode).toBe("groupByCategory");
    expect(resolveChartDataPolicy("pie").defaultAggregation).toBe("sum");
    expect(resolveChartDataPolicy("doughnut").rowMode).toBe("groupByCategory");
    expect(resolveChartDataPolicy("doughnut").defaultAggregation).toBe("sum");
  });

  it("resolveChartSeriesDefaultAggregation: número→soma; texto→contagem", () => {
    const pie = resolveChartDataPolicy("pie");
    expect(resolveChartSeriesDefaultAggregation(pie, "number")).toBe("sum");
    expect(resolveChartSeriesDefaultAggregation(pie, "string")).toBe("count");
    expect(resolveChartSeriesDefaultAggregation(pie, "date")).toBe("count");
    expect(resolveChartSeriesDefaultAggregation(pie, null)).toBe("sum");
  });

  it("linha/área permanecem rowwise", () => {
    expect(resolveChartDataPolicy("line").rowMode).toBe("rowwise");
    expect(resolveChartDataPolicy("area").rowMode).toBe("rowwise");
  });

  it("bar/horizontal_bar multi-série com wells SERIES", () => {
    expect(resolveChartDataPolicy("bar").maxSeries).toBe(6);
    expect(resolveChartDataPolicy("bar").maxCategories).toBeUndefined();
    expect(resolveChartDataPolicy("bar").wells.some((w) => w.role === "series")).toBe(true);
    expect(resolveChartDataPolicy("horizontal_bar").maxSeries).toBe(6);
    expect(resolveChartDataPolicy("horizontal_bar").maxCategories).toBeUndefined();
    expect(resolveChartDataPolicy("horizontal_bar").rowMode).toBe("groupByCategory");
    expect(resolveChartDataPolicy("stacked_bar").maxCategories).toBeUndefined();
  });

  it("pizza mantém soft-cap com bucket Outros", () => {
    expect(resolveChartDataPolicy("pie").maxCategories).toBe(8);
    expect(resolveChartDataPolicy("doughnut").maxCategories).toBe(8);
  });

  it("scatter/bubble são rowwise; histogram bins", () => {
    expect(resolveChartDataPolicy("scatter").rowMode).toBe("rowwise");
    expect(resolveChartDataPolicy("bubble").rowMode).toBe("rowwise");
    expect(resolveChartDataPolicy("histogram").rowMode).toBe("bins");
  });

  it("hint de pizza menciona fatias", () => {
    const hint = chartAxesEditorHint(resolveChartDataPolicy("pie"), true);
    expect(hint.toLowerCase()).toContain("fatia");
  });

  it("gauge: special, valor + well goal, agregação first", () => {
    const policy = resolveChartDataPolicy("gauge");
    expect(policy.family).toBe("special");
    expect(policy.rowMode).toBe("rowwise");
    expect(policy.defaultAggregation).toBe("first");
    expect(policy.maxSeries).toBe(1);
    expect(policy.wells.some((w) => w.role === "value")).toBe(true);
    expect(policy.wells.some((w) => w.role === "goal")).toBe(true);
  });

  it("tipos cartesianos com meta incluem well goal", () => {
    for (const chartType of ["line", "bar", "combo", "histogram"] as const) {
      expect(
        resolveChartDataPolicy(chartType).wells.some((w) => w.role === "goal"),
        chartType,
      ).toBe(true);
    }
  });

  it("pizza/funnel não têm well goal (sem linha de meta)", () => {
    expect(resolveChartDataPolicy("pie").wells.some((w) => w.role === "goal")).toBe(false);
    expect(resolveChartDataPolicy("funnel").wells.some((w) => w.role === "goal")).toBe(false);
  });
});
