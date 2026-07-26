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
  });
});
