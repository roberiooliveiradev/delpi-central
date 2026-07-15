import { describe, expect, it } from "vitest";

import {
  createDefaultFilterFormState,
  filtersFromFormState,
} from "./dateRange";

describe("filtersFromFormState", () => {
  it("omite filtros opcionais vazios", () => {
    const form = createDefaultFilterFormState(new Date("2026-07-15T12:00:00"));
    const result = filtersFromFormState("01", form);

    expect(result.filial).toBe("01");
    expect(result.dataInicio).toBe("2026-07-01");
    expect(result.dataFim).toBe("2026-07-15");
    expect(result.mp).toBeUndefined();
    expect(result.pa).toBeUndefined();
    expect(result.op).toBeUndefined();
    expect(result.motivo).toBeUndefined();
    expect(result.centroTrabalho).toBeUndefined();
  });

  it("mantém filtros opcionais preenchidos", () => {
    const result = filtersFromFormState("02", {
      dataInicio: "2026-04-01",
      dataFim: "2026-04-27",
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
