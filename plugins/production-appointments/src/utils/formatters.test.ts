import { describe, expect, it } from "vitest";

import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatProtheusDate,
  formatQuantity,
} from "./formatters";
import { getThisMonthRange, validatePeriodRange } from "./dateRange";

describe("formatters", () => {
  it("formata moeda, data e quantidade (sem conversão de unidade)", () => {
    expect(formatCurrencyBrl(10.5)).toMatch(/R\$/);
    expect(formatDatePtBr("2026-04-27")).toBe("27/04/2026");
    expect(formatProtheusDate("20260715")).toBe("15/07/2026");
    expect(formatQuantity(3836)).toBe("3.836,00");
  });
});

describe("dateRange", () => {
  it("valida período e default do mês", () => {
    expect(validatePeriodRange("2026-04-01", "2026-04-27")).toBeNull();
    expect(validatePeriodRange("2026-05-01", "2026-04-01")).toMatch(/inicial/);
    const range = getThisMonthRange(new Date(2026, 3, 15));
    expect(range.dateStart).toBe("2026-04-01");
    expect(range.dateEnd).toBe("2026-04-15");
  });
});
