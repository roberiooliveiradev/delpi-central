import { describe, expect, it } from "vitest";

import { resolveKpiViewPresentation } from "./resolveKpiPresentation";

describe("resolveKpiViewPresentation", () => {
  it("calcula comparação vs meta e progresso", () => {
    const presentation = resolveKpiViewPresentation(
      {
        kpi: { value: 110, label: "OEE" },
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
    expect(presentation.valueText).toContain("110");
    expect(presentation.comparisonText).toMatch(/vs meta/);
    expect(presentation.comparisonTone).toBe("positive");
    expect(presentation.progressPct).toBeCloseTo(110);
  });

  it("expõe sparkline a partir da série do resolved", () => {
    const presentation = resolveKpiViewPresentation(
      {
        kpi: { value: 85, label: "OEE" },
        chart: { points: [{ value: 70 }, { value: 75 }, { value: 85 }] },
      },
      { showSparkline: true },
    );
    expect(presentation.sparklinePoints).toEqual([70, 75, 85]);
  });

  it("comparação vs período usa penúltimo ponto", () => {
    const presentation = resolveKpiViewPresentation(
      {
        kpi: { value: 80, label: "Scrap" },
        chart: { points: [{ value: 100 }, { value: 90 }, { value: 80 }] },
      },
      {
        comparisonMode: "previous",
        showComparison: true,
        higherIsBetter: false,
      },
    );
    expect(presentation.comparisonText).toMatch(/vs período/);
    expect(presentation.comparisonTone).toBe("positive");
  });
});
