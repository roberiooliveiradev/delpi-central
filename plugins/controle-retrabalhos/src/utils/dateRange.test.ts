import { describe, expect, it } from "vitest";

import {
  createDefaultFilterFormState,
  getDefaultLast12MonthsRange,
  getDefaultLast6MonthsRange,
  getThisMonthRange,
  validatePeriodRange,
} from "./dateRange";

describe("dateRange", () => {
  it("default range spans 12 calendar months", () => {
    const ref = new Date(2026, 6, 6);
    const range = getDefaultLast12MonthsRange(ref);
    expect(range.dataInicio).toBe("2025-08-01");
    expect(range.dataFim).toBe("2026-07-06");
  });

  it("last 6 months range spans 6 calendar months", () => {
    const ref = new Date(2026, 6, 6);
    const range = getDefaultLast6MonthsRange(ref);
    expect(range.dataInicio).toBe("2026-02-01");
    expect(range.dataFim).toBe("2026-07-06");
  });

  it("this month range starts on first day of current month", () => {
    const ref = new Date(2026, 6, 6);
    const range = getThisMonthRange(ref);
    expect(range.dataInicio).toBe("2026-07-01");
    expect(range.dataFim).toBe("2026-07-06");
  });

  it("rejects periods longer than 24 months", () => {
    const error = validatePeriodRange("2020-01-01", "2026-07-06");
    expect(error).toMatch(/24 meses/);
  });

  it("createDefaultFilterFormState matches helper", () => {
    const ref = new Date(2026, 0, 15);
    expect(createDefaultFilterFormState(ref)).toEqual(getDefaultLast12MonthsRange(ref));
  });
});
