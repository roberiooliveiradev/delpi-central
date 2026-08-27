import { describe, expect, it } from "vitest";

import { resolveGaugeChartModel } from "./gaugeChartModel";

describe("resolveGaugeChartModel", () => {
  it("lê valor do kpi e meta do override", () => {
    const model = resolveGaugeChartModel({
      block: {
        chartOptions: { goalLineValue: 95, seriesColor: "#089bdb", showTitle: true, title: "OTD" },
      },
      resolved: {
        label: "OTD",
        kpi: { value: 98.8, label: "OTD SC" },
      },
    });
    expect(model.value).toBe(98.8);
    expect(model.goal).toBe(95);
    expect(model.accentColor).toBe("#089bdb");
    expect(model.title).toBe("OTD");
  });

  it("meta da coluna via projectedGoal quando sem override", () => {
    const model = resolveGaugeChartModel({
      block: { chartOptions: { showGoalLine: true } },
      resolved: {
        kpi: { value: 88, label: "OTD" },
        chart: { projectedGoal: 92 },
      },
    });
    expect(model.value).toBe(88);
    expect(model.goal).toBe(92);
  });

  it("manual sobrescreve projectedGoal", () => {
    const model = resolveGaugeChartModel({
      block: { chartOptions: { goalLineValue: 99 } },
      resolved: {
        kpi: { value: 80 },
        chart: { projectedGoal: 90 },
      },
    });
    expect(model.goal).toBe(99);
  });
});
