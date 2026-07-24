import { describe, expect, it } from "vitest";

import type { DashboardEvolucaoItem } from "../data/api/transformometroApi";
import { buildEvolucaoSavingsSeries } from "./evolucaoChartSeries";

describe("buildEvolucaoSavingsSeries", () => {
  it("visão dia: usa pontos diários da API sem ratear", () => {
    const items: DashboardEvolucaoItem[] = [
      {
        competencia: "2026-04-01",
        economia_bruta: 10,
        economia_liquida_mes: 10,
        investimento_total_mes: 0,
        horas_economizadas_mes: 1,
      },
      {
        competencia: "2026-04-16",
        economia_bruta: 20,
        economia_liquida_mes: -50,
        investimento_unico_mes: 70,
        investimento_total_mes: 70,
        horas_economizadas_mes: 2,
      },
    ];

    const { points, dayProrated } = buildEvolucaoSavingsSeries(
      items,
      "2026-04-01",
      "2026-04-30",
      "day",
    );

    expect(dayProrated).toBe(false);
    expect(points).toHaveLength(30);
    expect(points.find((p) => p.sortKey === "2026-04-01")?.bruta).toBe(10);
    expect(points.find((p) => p.sortKey === "2026-04-16")?.bruta).toBe(20);
    expect(points.find((p) => p.sortKey === "2026-04-16")?.investimento).toBe(70);
    expect(points.find((p) => p.sortKey === "2026-04-02")?.bruta).toBe(0);
  });

  it("visão mês: agrega competências YYYY-MM", () => {
    const items: DashboardEvolucaoItem[] = [
      {
        competencia: "2026-04",
        economia_bruta: 100,
        economia_liquida_mes: 80,
        investimento_total_mes: 20,
        horas_economizadas_mes: 10,
      },
    ];

    const { points } = buildEvolucaoSavingsSeries(
      items,
      "2026-04-01",
      "2026-04-30",
      "month",
    );

    expect(points).toHaveLength(1);
    expect(points[0].bruta).toBe(100);
    expect(points[0].investimento).toBe(20);
  });
});
