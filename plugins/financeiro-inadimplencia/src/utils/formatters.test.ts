import { describe, expect, it } from "vitest";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatInteger,
  formatMonthYearPtBr,
  formatPercent,
  formatTituloLabel,
} from "./formatters";

describe("formatters", () => {
  it("formata moeda e percentual em pt-BR", () => {
    expect(formatCurrencyBrl(5552009.4)).toMatch(/R\$\s?5\.552\.009,40/);
    expect(formatPercent(92.03)).toBe("92,03%");
    expect(formatInteger(6111)).toBe("6.111");
  });

  it("formata datas e mês", () => {
    expect(formatDatePtBr("2026-02-05")).toBe("05/02/2026");
    expect(formatMonthYearPtBr("2025-07")).toBe("Jul/2025");
  });

  it("monta título sem barras vazias", () => {
    expect(formatTituloLabel("02", "014413", "")).toBe("02 / 014413");
    expect(formatTituloLabel("02", "014413", "A")).toBe("02 / 014413 / A");
  });
});
