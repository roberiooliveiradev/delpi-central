import { describe, expect, it } from "vitest";

import {
  detectDelinquencyPeriodPreset,
  resolveDelinquencyPeriodPreset,
} from "./delinquencyPeriodPresets";

const REF = new Date(2026, 7, 22);

describe("resolveDelinquencyPeriodPreset", () => {
  it("resolve este mês com fim inclusivo em hoje", () => {
    expect(resolveDelinquencyPeriodPreset("this_month", REF)).toEqual({
      startDate: "2026-08-01",
      endDate: "2026-08-22",
    });
  });

  it("resolve este semestre a partir de julho", () => {
    expect(resolveDelinquencyPeriodPreset("this_semester", REF)).toEqual({
      startDate: "2026-07-01",
      endDate: "2026-08-22",
    });
  });

  it("resolve este ano", () => {
    expect(resolveDelinquencyPeriodPreset("this_year", REF)).toEqual({
      startDate: "2026-01-01",
      endDate: "2026-08-22",
    });
  });
});

describe("detectDelinquencyPeriodPreset", () => {
  it("reconhece preset ativo", () => {
    expect(detectDelinquencyPeriodPreset("2026-08-01", "2026-08-22", REF)).toBe("this_month");
  });

  it("retorna null para intervalo customizado", () => {
    expect(detectDelinquencyPeriodPreset("2026-08-01", "2026-08-21", REF)).toBeNull();
  });
});
