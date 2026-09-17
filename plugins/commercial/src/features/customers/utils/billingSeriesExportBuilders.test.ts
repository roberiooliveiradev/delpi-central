import { describe, expect, it } from "vitest";

import { buildBillingSeriesExportPayload } from "./billingSeriesExportBuilders";

describe("buildBillingSeriesExportPayload", () => {
  const points = [
    {
      periodo: "01/09/26",
      faturamento: 1000,
      quantidade: 12.5,
    },
  ];

  it("value exporta só faturamento em R$", () => {
    const payload = buildBillingSeriesExportPayload(points, { title: "Fat" });
    expect(payload.columns.map((column) => column.key)).toEqual([
      "periodo",
      "faturamento",
    ]);
    expect(String(payload.rows[0]?.faturamento)).toMatch(/R\$/);
    expect(payload.rows[0]).not.toHaveProperty("quantidade");
  });

  it("quantity formata a coluna primária como qtd", () => {
    const payload = buildBillingSeriesExportPayload(points, {
      title: "Qtd",
      metric: "quantity",
    });
    expect(payload.columns[1]?.label).toBe("Quantidade");
    expect(String(payload.rows[0]?.faturamento)).toMatch(/1\.000,000/);
  });

  it("both exporta faturamento e quantidade juntos", () => {
    const payload = buildBillingSeriesExportPayload(points, {
      title: "Ambos",
      metric: "both",
    });
    expect(payload.columns.map((column) => column.key)).toEqual([
      "periodo",
      "faturamento",
      "quantidade",
    ]);
    expect(String(payload.rows[0]?.faturamento)).toMatch(/R\$/);
    expect(String(payload.rows[0]?.quantidade)).toMatch(/12,500/);
  });

  it("Ambos + ano anterior exporta quantidade do período comparado", () => {
    const payload = buildBillingSeriesExportPayload(
      [
        {
          periodo: "Fev. de 26",
          faturamento: 151000,
          quantidade: 554.47,
          faturamento_prior: 100000,
          quantidade_prior: 400,
        },
      ],
      { title: "Ambos", metric: "both", compareYears: 1, unit: "MI" },
    );
    expect(payload.columns.map((column) => column.key)).toEqual([
      "periodo",
      "faturamento",
      "quantidade",
      "prior1",
      "qtyPrior1",
    ]);
    expect(String(payload.rows[0]?.qtyPrior1)).toBe("400,000 MI");
  });

  it("value + ano anterior não cria coluna de quantidade prior", () => {
    const payload = buildBillingSeriesExportPayload(points, {
      title: "Fat",
      compareYears: 1,
    });
    expect(payload.columns.map((column) => column.key)).not.toContain("qtyPrior1");
  });

  it("anexa a UM nas células de quantidade", () => {
    const payload = buildBillingSeriesExportPayload(points, {
      title: "Qtd",
      metric: "quantity",
      unit: "MI",
    });
    expect(String(payload.rows[0]?.faturamento)).toBe("1.000,000 MI");
    const both = buildBillingSeriesExportPayload(points, {
      title: "Ambos",
      metric: "both",
      unit: "PC",
    });
    expect(String(both.rows[0]?.quantidade)).toBe("12,500 PC");
  });
});
