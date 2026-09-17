import { describe, expect, it } from "vitest";

import { mergeBillingSeriesOverlays } from "./mergeBillingSeriesOverlays";

function point(month: string, value: number) {
  return {
    month,
    label: month,
    value,
    date_start: `${month}-01`,
    date_end: `${month}-28`,
  };
}

describe("mergeBillingSeriesOverlays", () => {
  it("positive: Ambos + ano anterior anexa quantidade corrente e prior", () => {
    const merged = mergeBillingSeriesOverlays({
      current: [point("2026-02", 151000), point("2026-03", 220000)],
      quantityPoints: [point("2026-02", 554.47), point("2026-03", 800)],
      priorValueSeries: [[point("2025-02", 100000), point("2025-03", 180000)]],
      priorQuantitySeries: [[point("2025-02", 400), point("2025-03", 700)]],
    });
    expect(merged[0]).toMatchObject({
      value: 151000,
      quantity: 554.47,
      value_prior: 100000,
      quantity_prior: 400,
    });
    expect(merged[1]).toMatchObject({
      value: 220000,
      quantity: 800,
      value_prior: 180000,
      quantity_prior: 700,
    });
  });

  it("sibling: YoY só de valor não inventa quantity_prior", () => {
    const merged = mergeBillingSeriesOverlays({
      current: [point("2026-02", 151000)],
      priorValueSeries: [[point("2025-02", 100000)]],
    });
    expect(merged[0]?.value_prior).toBe(100000);
    expect(merged[0]?.quantity).toBeUndefined();
    expect(merged[0]?.quantity_prior).toBeUndefined();
  });

  it("negative: sem overlay de quantidade o recorte em R$ permanece só valor", () => {
    const merged = mergeBillingSeriesOverlays({
      current: [point("2026-02", 151000)],
    });
    expect(merged[0]?.value).toBe(151000);
    expect(merged[0]?.quantity).toBeUndefined();
    expect(merged[0]?.quantity_prior).toBeUndefined();
    expect(merged[0]?.value_prior).toBeUndefined();
  });
});
