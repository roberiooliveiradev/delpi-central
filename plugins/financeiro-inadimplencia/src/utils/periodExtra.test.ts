import { describe, expect, it } from "vitest";

import {
  createDefaultPeriodFormState,
  periodFilterFromForm,
  resolvePeriodPreset,
  validatePeriodRange,
} from "./period";

describe("filtros de período (fim exclusivo)", () => {
  it("ano atual inclui o mês corrente (fim exclusivo = dia 1 do próximo mês)", () => {
    const range = resolvePeriodPreset("current_year", new Date(2026, 6, 14));
    expect(range.startDate).toBe("2026-01-01");
    expect(range.endDate).toBe("2026-08-01");
  });

  it("ano anterior fecha em 1º de janeiro do ano corrente (exclusivo)", () => {
    const range = resolvePeriodPreset("previous_year", new Date(2026, 6, 14));
    expect(range).toEqual({
      startDate: "2025-01-01",
      endDate: "2026-01-01",
    });
  });

  it("personalizado rejeita início igual ao fim e início posterior ao fim", () => {
    expect(validatePeriodRange("2026-01-01", "2026-01-01")).toMatch(/anterior/);
    expect(validatePeriodRange("2026-02-01", "2026-01-01")).toMatch(/anterior/);
  });

  it("default envia datas que incluem o mês atual", () => {
    const form = createDefaultPeriodFormState(new Date(2026, 6, 14));
    expect(periodFilterFromForm(form)).toEqual({
      startDate: "2025-08-01",
      endDate: "2026-08-01",
    });
  });
});
