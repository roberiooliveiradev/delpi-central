import { describe, expect, it } from "vitest";

import { formatCurrencyBrl, formatDatePtBr, formatRankingAxisLabel } from "./formatters";
import { getThisMonthRange, validatePeriodRange } from "./dateRange";

describe("formatters", () => {
  it("formata moeda e data", () => {
    expect(formatCurrencyBrl(10.5)).toMatch(/R\$/);
    expect(formatDatePtBr("2026-04-27")).toBe("27/04/2026");
  });

  it("monta rótulo de ranking com código", () => {
    expect(formatRankingAxisLabel("90480001", "CHICOTE TESTE", 40)).toContain("90480001");
    expect(formatRankingAxisLabel("90480001", "CHICOTE TESTE", 40)).toContain("—");
  });
});

describe("dateRange", () => {
  it("valida período e default do mês", () => {
    expect(validatePeriodRange("2026-04-01", "2026-04-27")).toBeNull();
    expect(validatePeriodRange("2026-05-01", "2026-04-01")).toMatch(/inicial/);
    const range = getThisMonthRange(new Date(2026, 3, 15));
    expect(range.dataInicio).toBe("2026-04-01");
    expect(range.dataFim).toBe("2026-04-15");
  });
});
