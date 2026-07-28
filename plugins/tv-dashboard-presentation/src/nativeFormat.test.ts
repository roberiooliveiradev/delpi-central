import { describe, expect, it } from "vitest";

import {
  formatCurrency,
  formatNumber,
  formatPct,
  formatSupportsDecimalPlaces,
  normalizeDecimalPlaces,
} from "./nativeFormat";

describe("nativeFormat (pt-BR)", () => {
  it("formatPct usa vírgula decimal", () => {
    expect(formatPct(0)).toBe("0,0%");
    expect(formatPct(80)).toBe("80,0%");
    expect(formatPct(12.5)).toBe("12,5%");
  });

  it("formatCurrency formata BRL", () => {
    expect(formatCurrency(4005.33)).toMatch(/R\$\s*4\.005,33/);
    expect(formatCurrency(0)).toMatch(/R\$\s*0,00/);
  });

  it("formatNumber usa vírgula decimal", () => {
    expect(formatNumber(315.47)).toBe("315,47");
  });

  it("casas decimais explícitas arredondam na exibição", () => {
    expect(formatNumber(1.235, 2)).toBe("1,24");
    expect(formatNumber(1.234, 2)).toBe("1,23");
    expect(formatNumber(99.9, 0)).toBe("100");
    expect(formatPct(12.56, 0)).toBe("13%");
    expect(formatPct(12.56, 2)).toBe("12,56%");
    expect(formatCurrency(10.556, 2)).toMatch(/R\$\s*10,56/);
    expect(formatCurrency(10.556, 0)).toMatch(/R\$\s*11/);
  });

  it("normalizeDecimalPlaces limita 0–6", () => {
    expect(normalizeDecimalPlaces(2)).toBe(2);
    expect(normalizeDecimalPlaces(2.9)).toBe(2);
    expect(normalizeDecimalPlaces(-1)).toBe(0);
    expect(normalizeDecimalPlaces(9)).toBe(6);
    expect(normalizeDecimalPlaces("x")).toBeUndefined();
  });

  it("formatSupportsDecimalPlaces só number/percent/currency", () => {
    expect(formatSupportsDecimalPlaces("number")).toBe(true);
    expect(formatSupportsDecimalPlaces("percent")).toBe(true);
    expect(formatSupportsDecimalPlaces("currency")).toBe(true);
    expect(formatSupportsDecimalPlaces("compact")).toBe(false);
    expect(formatSupportsDecimalPlaces("raw")).toBe(false);
  });
});
