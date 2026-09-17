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
});
