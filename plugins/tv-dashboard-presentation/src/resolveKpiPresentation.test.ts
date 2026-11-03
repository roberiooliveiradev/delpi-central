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

  it("pinta status posicional do backend junto da comparação sem recalcular meta", () => {
    const presentation = resolveKpiViewPresentation(
      {
        kpi: { value: 93.73, label: "OEE realizado", displayValue: "93,73%" },
        kpiPresentation: {
          valueDisplay: "93,73%",
          comparisonDisplay: "▲ +8,73 p.p. vs meta",
          comparisonTone: "positive",
          statusLabel: "Acima da meta",
          showComparison: true,
        },
      },
      { comparisonMode: "target", showComparison: true, variant: "hero" },
    );
    expect(presentation.valueText).toBe("93,73%");
    expect(presentation.comparisonText).toBe("▲ +8,73 p.p. vs meta · Acima da meta");
    expect(presentation.comparisonTone).toBe("positive");
  });

  it("preserva apresentação legada e não cria status quando o backend não entregou", () => {
    const presentation = resolveKpiViewPresentation({
      kpi: { value: 91, label: "OEE", displayValue: "91,00%" },
      kpiPresentation: {
        comparisonDisplay: "▼ −2,00 p.p. vs meta",
        comparisonTone: "negative",
        showComparison: true,
      },
    });
    expect(presentation.comparisonText).toBe("▼ −2,00 p.p. vs meta");
    expect(presentation.comparisonTone).toBe("negative");
  });

  it("não exibe status stale se backend desabilitou comparação", () => {
    const presentation = resolveKpiViewPresentation({
      kpi: { value: 85, label: "Meta", displayValue: "85,00%" },
      kpiPresentation: {
        statusLabel: "Na meta",
        comparisonDisplay: null,
        showComparison: false,
      },
    });
    expect(presentation.comparisonText).toBeUndefined();
  });

  it("não duplica texto quando status já compõe comparisonDisplay no servidor", () => {
    const presentation = resolveKpiViewPresentation({
      kpi: { value: 93, label: "OEE", displayValue: "93,00%" },
      kpiPresentation: {
        comparisonDisplay: "▲ +8,00 p.p. vs meta · Acima da meta",
        statusLabel: "Acima da meta",
        showComparison: true,
      },
    });
    expect(presentation.comparisonText).toBe("▲ +8,00 p.p. vs meta · Acima da meta");
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
