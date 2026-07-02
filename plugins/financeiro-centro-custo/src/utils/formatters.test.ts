import { describe, expect, it } from "vitest";

import {
  formatCostCenterLabel,
  formatCurrencyBrl,
  formatDatePtBr,
  formatMonthYearPtBr,
  formatPercent,
  formatSupplierLabel,
} from "./formatters";

describe("formatters", () => {
  it("formata moeda em BRL", () => {
    expect(formatCurrencyBrl(1234.5)).toMatch(/R\$\s?1\.234,50/);
  });

  it("formata data ISO em pt-BR", () => {
    expect(formatDatePtBr("2026-06-30")).toBe("30/06/2026");
  });

  it("formata data Protheus YYYYMMDD em pt-BR", () => {
    expect(formatDatePtBr("20260624")).toBe("24/06/2026");
  });

  it("formata data já em DD/MM/AAAA", () => {
    expect(formatDatePtBr("24/06/2026")).toBe("24/06/2026");
  });

  it("formata mês compacto YYYYMM como Jan/2026", () => {
    expect(formatMonthYearPtBr("202601")).toBe("Jan/2026");
    expect(formatMonthYearPtBr("202603")).toBe("Mar/2026");
    expect(formatMonthYearPtBr("202508")).toBe("Ago/2025");
  });

  it("formata mês ISO YYYY-MM como Jan/2026", () => {
    expect(formatMonthYearPtBr("2026-01")).toBe("Jan/2026");
  });

  it("monta rótulo de fornecedor", () => {
    expect(formatSupplierLabel("003287", "01", "Fornecedor Teste")).toBe(
      "Fornecedor Teste (003287/01)",
    );
  });

  it("monta rótulo de centro de custo", () => {
    expect(formatCostCenterLabel("0101", "Administrativo")).toBe("0101 — Administrativo");
  });

  it("formata percentual com uma casa decimal", () => {
    expect(formatPercent(12.345)).toBe("12,3%");
    expect(formatPercent(null)).toBe("—");
  });
});
