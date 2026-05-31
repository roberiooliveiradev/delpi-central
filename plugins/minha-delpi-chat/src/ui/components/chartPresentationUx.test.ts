import { describe, expect, it } from "vitest";

import {
  applyChartZoomWindow,
  buildPeriodComparisonRows,
  detectPeriodCompare,
  isTemporalChartAxis,
} from "./chartPresentationUx";

describe("chartPresentationUx", () => {
  it("detecta eixo temporal por rótulos de mês", () => {
    const data = [
      { mes: "2026-01", valor: 1 },
      { mes: "2026-02", valor: 2 },
      { mes: "2026-03", valor: 3 },
    ];

    expect(isTemporalChartAxis("mes", data)).toBe(true);
  });

  it("aplica zoom na cauda da série", () => {
    const data = [{ n: 1 }, { n: 2 }, { n: 3 }, { n: 4 }];

    expect(applyChartZoomWindow(data, "2")).toEqual([{ n: 3 }, { n: 4 }]);
  });

  it("monta comparação por período", () => {
    const data = [
      { mes: "Jan", period: "2024", valor: 10 },
      { mes: "Jan", period: "2025", valor: 14 },
      { mes: "Fev", period: "2024", valor: 8 },
      { mes: "Fev", period: "2025", valor: 11 },
    ];

    const spec = detectPeriodCompare(data, "mes", "valor");

    expect(spec?.periods).toEqual(["2024", "2025"]);

    const { rows, yAxes } = buildPeriodComparisonRows(data, spec!);

    expect(yAxes).toEqual(["2024", "2025"]);
    expect(rows).toHaveLength(2);
    expect(rows[0]["2025"]).toBe(14);
  });
});
