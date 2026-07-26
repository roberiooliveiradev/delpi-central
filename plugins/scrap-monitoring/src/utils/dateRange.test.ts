import { describe, expect, it } from "vitest";

import {
  createDefaultFilterFormState,
  filtersFromFormState,
  getThisWeekRange,
  getTodayRange,
} from "./dateRange";

describe("filtersFromFormState", () => {
  it("omite filtros opcionais vazios", () => {
    const form = createDefaultFilterFormState(new Date("2026-07-15T12:00:00"));
    const result = filtersFromFormState("01", form);

    expect(result.filial).toBe("01");
    expect(result.start_date).toBe("2026-07-01");
    expect(result.end_date).toBe("2026-07-15");
    expect(result.mp).toBeUndefined();
    expect(result.pa).toBeUndefined();
    expect(result.op).toBeUndefined();
    expect(result.motivo).toBeUndefined();
    expect(result.centroTrabalho).toBeUndefined();
  });

  it("mantém filtros opcionais preenchidos", () => {
    const result = filtersFromFormState("02", {
      start_date: "2026-04-01",
      end_date: "2026-04-27",
      mp: " 90001234 ",
      pa: "PA01",
      op: "OP1",
      motivo: "FM",
      centroTrabalho: "CT-23",
    });

    expect(result).toMatchObject({
      filial: "02",
      mp: "90001234",
      pa: "PA01",
      op: "OP1",
      motivo: "FM",
      centroTrabalho: "CT-23",
    });
  });
});

describe("quick ranges hoje e semana", () => {
  it("hoje usa o mesmo dia em início e fim", () => {
    expect(getTodayRange(new Date("2026-07-15T18:30:00"))).toEqual({
      start_date: "2026-07-15",
      end_date: "2026-07-15",
    });
  });

  it("esta semana vai de segunda até o dia de referência", () => {
    // 15/07/2026 é quarta → segunda = 13/07
    expect(getThisWeekRange(new Date("2026-07-15T12:00:00"))).toEqual({
      start_date: "2026-07-13",
      end_date: "2026-07-15",
    });
  });

  it("domingo da semana vai à segunda anterior", () => {
    // 12/07/2026 é domingo → segunda = 06/07
    expect(getThisWeekRange(new Date("2026-07-12T12:00:00"))).toEqual({
      start_date: "2026-07-06",
      end_date: "2026-07-12",
    });
  });
});
