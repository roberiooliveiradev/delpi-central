import { describe, expect, it } from "vitest";

import { applyDataParamRawUpdates, parseDataParamRaw } from "./applyDataParamUpdates";

describe("applyDataParamRawUpdates", () => {
  it("aplica dateRangePreset e limpa competence no mesmo patch", () => {
    const next = applyDataParamRawUpdates(
      { dateRangePreset: "this_month", competence: "2026-06", branch: "01" },
      { dateRangePreset: "this_year", competence: "" },
      {
        competence: { type: "string" },
        branch: { type: "string" },
      },
    );
    expect(next).toEqual({
      dateRangePreset: "this_year",
      branch: "01",
    });
    expect(next).not.toHaveProperty("competence");
  });

  it("parseia inteiros do schema", () => {
    expect(parseDataParamRaw("periodDays", "15", { periodDays: { type: "integer" } })).toBe(15);
    expect(parseDataParamRaw("excludeWeekends", "true", {})).toBe(true);
    expect(parseDataParamRaw("excludeWeekends", "", {})).toBeUndefined();
  });

  it("rejeita data com ano absurdo (ex.: 0026)", () => {
    expect(
      parseDataParamRaw("start_date", "0026-07-01", {
        start_date: { type: "string", format: "date" },
        end_date: { type: "string", format: "date" },
      }),
    ).toBeUndefined();
    expect(
      parseDataParamRaw("start_date", "2026-07-01", {
        start_date: { type: "string", format: "date" },
        end_date: { type: "string", format: "date" },
      }),
    ).toBe("2026-07-01");
  });
});
