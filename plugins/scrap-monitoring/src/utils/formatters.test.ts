import { describe, expect, it } from "vitest";

import {
  formatCodeWithLabel,
  formatCurrencyBrl,
  formatDatePtBr,
  formatRankingAxisLabel,
  resolveUnitCost,
  splitRankingAxisLines,
} from "./formatters";
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

  it("separa código e descrição em duas linhas", () => {
    const lines = splitRankingAxisLines("10070344", "CABO PP CIRCULAR PVC/PVC 9X22AWG");
    expect(lines.codeLine).toBe("10070344");
    expect(lines.descLine).toContain("CABO PP");
  });

  it("resolve custo unitário explícito ou derivado", () => {
    expect(resolveUnitCost(10, 2, 5)).toBe(5);
    expect(resolveUnitCost(10, 2)).toBe(5);
    expect(resolveUnitCost(10, 0)).toBeNull();
    expect(formatCodeWithLabel("9048", "Chicote")).toBe("9048 — Chicote");
  });
});

describe("dateRange", () => {
  it("valida período e default do mês", () => {
    expect(validatePeriodRange("2026-04-01", "2026-04-27")).toBeNull();
    expect(validatePeriodRange("2026-05-01", "2026-04-01")).toMatch(/inicial/);
    const range = getThisMonthRange(new Date(2026, 3, 15));
    expect(range.start_date).toBe("2026-04-01");
    expect(range.end_date).toBe("2026-04-15");
  });
});
