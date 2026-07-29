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

  it("comparação e funil agrupam por categoria", () => {
    expect(resolveChartDataPolicy("bar").rowMode).toBe("groupByCategory");
    expect(resolveChartDataPolicy("stacked_bar").rowMode).toBe("groupByCategory");
    expect(resolveChartDataPolicy("funnel").rowMode).toBe("groupByCategory");
    expect(resolveChartDataPolicy("waterfall").rowMode).toBe("groupByCategory");
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
});
