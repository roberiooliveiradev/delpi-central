import { describe, expect, it } from "vitest";

import {
  EMPTY_VALUE,
  formatCompactCurrency,
  formatCurrency,
  formatDays,
  formatIndicatorValue,
  formatInteger,
  formatPercent,
  formatScore,
} from "./formatNumbers";

describe("formatNumbers", () => {
  it("formats currency and compact currency in pt-BR", () => {
    expect(formatCurrency(1500)).toMatch(/R\$/);
    expect(formatCompactCurrency(5_000_000)).toMatch(/R\$/);
    expect(formatCurrency(undefined)).toBe(EMPTY_VALUE);
  });

  it("formats percent, days and score", () => {
    expect(formatPercent(80)).toBe("80,0%");
    expect(formatDays(1)).toBe("1 dia");
    expect(formatDays(4)).toBe("4 dias");
    expect(formatScore(8.4)).toBe("8,4");
    expect(formatInteger(320)).toBe("320");
  });

  it("formats indicator values with unit and decimals", () => {
    expect(formatIndicatorValue(18.4, { unit: "%", decimals: 1 })).toBe("18,4%");
    expect(formatIndicatorValue(null)).toBe(EMPTY_VALUE);
  });
});
