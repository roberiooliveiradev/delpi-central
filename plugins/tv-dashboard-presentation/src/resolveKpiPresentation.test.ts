import { describe, expect, it } from "vitest";

import { resolveKpiViewPresentation } from "./resolveKpiPresentation";

describe("resolveKpiViewPresentation", () => {
  it("usa kpiPresentation do enrich para comparação/progresso", () => {
    const presentation = resolveKpiViewPresentation(
      {
        kpi: { value: 110, label: "OEE", displayValue: "110" },
        kpiPresentation: {
          valueDisplay: "110",
          comparisonDisplay: "▲ +10,0% vs meta",
          comparisonTone: "positive",
          progressPct: 110,
          showSparkline: false,
          showComparison: true,
          showProgress: true,
        },
        chart: { points: [{ value: 90 }, { value: 100 }, { value: 110 }] },
      },
      {
        title: "OEE",
        target: 100,
        comparisonMode: "target",
        showComparison: true,
        showProgress: true,
        higherIsBetter: true,
      },
    );
    expect(presentation.valueText).toBe("110");
    expect(presentation.comparisonText).toMatch(/vs meta/);
    expect(presentation.comparisonTone).toBe("positive");
    expect(presentation.progressPct).toBeCloseTo(110);
  });

  it("expõe sparkline do enrich ou da série do resolved", () => {
    const presentation = resolveKpiViewPresentation(
      {
        kpi: { value: 85, label: "OEE", displayValue: "85" },
        kpiPresentation: {
          valueDisplay: "85",
          sparklinePoints: [70, 75, 85],
          showSparkline: true,
        },
        chart: { points: [{ value: 70 }, { value: 75 }, { value: 85 }] },
      },
      { showSparkline: true },
    );
    expect(presentation.sparklinePoints).toEqual([70, 75, 85]);
  });

  it("prefere kpi.displayValue do enrich sem reformatar", () => {
    const presentation = resolveKpiViewPresentation(
      { kpi: { value: 41.7, label: "OEE", displayValue: "SERVER-41,7%" } },
      { valueFormat: "number", decimalPlaces: 0 },
    );
    expect(presentation.valueText).toBe("SERVER-41,7%");
  });

  it("multi-métrica: kpi.displayValue vence kpiPresentation do primary", () => {
    const presentation = resolveKpiViewPresentation({
      kpi: { value: 87.3, label: "Atingimento", displayValue: "87,3%" },
      kpiPresentation: {
        valueDisplay: "4.364.622,79",
        showComparison: false,
      },
    });
    expect(presentation.valueText).toBe("87,3%");
  });

  it("sem display* pinta unresolved (sem format client)", () => {
    const presentation = resolveKpiViewPresentation(
      { kpi: { value: 41.7, label: "OEE" } },
      { valueFormat: "percent", decimalPlaces: 1 },
    );
    expect(presentation.valueText).toBe("—");
    expect(presentation.comparisonText).toBeUndefined();
  });
});
