import { describe, expect, it } from "vitest";

import { buildCustomerHeroHighlights } from "./customerHeroHighlights";

describe("buildCustomerHeroHighlights", () => {
  it("monta os quatro fatos do hero sem inventar faturamento", () => {
    const result = buildCustomerHeroHighlights({
      billed12m: 34025,
      billingTrend: "up",
      billingTrendPct: 14.7,
      valorTotalAberto: 1555,
      quantidadePedidosAbertos: 1,
      proximaEntrega: "2026-08-15",
      nextAction: "Tratar atraso",
    });

    expect(result.highlights.map((item) => item.id)).toEqual([
      "billed12m",
      "open-value",
      "open-orders",
      "next-delivery",
    ]);
    expect(result.highlights[0]?.value).toContain("34.025");
    expect(result.highlights[0]?.value).toContain("↑");
    expect(result.nextAction).toBe("Tratar atraso");
  });

  it("não transforma faturamento ausente em zero", () => {
    const result = buildCustomerHeroHighlights({
      billed12m: null,
      billingTrend: null,
      billingTrendPct: null,
      valorTotalAberto: 0,
      quantidadePedidosAbertos: 2,
      proximaEntrega: null,
      nextAction: "   ",
    });
    expect(result.highlights[0]?.value).toBe("—");
    expect(result.nextAction).toBeNull();
  });
});
