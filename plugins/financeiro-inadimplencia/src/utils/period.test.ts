import { describe, expect, it } from "vitest";
import {
  createDefaultPeriodFormState,
  getCurrentMonthRange,
  getLastCompleteMonthsRange,
  getLastMonthsRangeIncludingCurrent,
  periodFilterFromForm,
  resolvePeriodPreset,
  validatePeriodRange,
} from "./period";

describe("period helpers", () => {
  it("calcula últimos 12 meses completos sem o mês corrente", () => {
    const range = getLastCompleteMonthsRange(12, new Date(2026, 6, 14));
    expect(range).toEqual({
      startDate: "2025-07-01",
      endDate: "2026-07-01",
    });
  });

  it("inclui o mês corrente nos últimos 12 meses", () => {
    const range = getLastMonthsRangeIncludingCurrent(12, new Date(2026, 6, 14));
    expect(range).toEqual({
      startDate: "2025-08-01",
      endDate: "2026-08-01",
    });
  });

  it("resolve preset de 6 meses incluindo o mês atual", () => {
    const range = resolvePeriodPreset("last_6_months", new Date(2026, 6, 14));
    expect(range).toEqual({
      startDate: "2026-02-01",
      endDate: "2026-08-01",
    });
  });

  it("envia datas explícitas no padrão de 12 meses (inclui mês atual)", () => {
    const form = createDefaultPeriodFormState(new Date(2026, 6, 14));
    expect(periodFilterFromForm(form)).toEqual({
      startDate: "2025-08-01",
      endDate: "2026-08-01",
    });
  });

  it("calcula o intervalo do mês civil corrente", () => {
    expect(getCurrentMonthRange(new Date(2026, 6, 14))).toEqual({
      startDate: "2026-07-01",
      endDate: "2026-08-01",
    });
  });

  it("valida intervalo inválido e limite máximo", () => {
    expect(validatePeriodRange("2026-07-01", "2025-07-01")).toMatch(/anterior/);
    expect(validatePeriodRange("2020-01-01", "2026-01-01")).toMatch(/60/);
    expect(validatePeriodRange("2025-07-01", "2026-07-01")).toBeNull();
  });
});
