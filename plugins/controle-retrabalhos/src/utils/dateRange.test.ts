import { describe, expect, it } from "vitest";

import {
  createDefaultFilterFormState,
  getDefaultLast12MonthsRange,
  getDefaultLast30DaysRange,
  getDefaultLast6MonthsRange,
  getThisMonthRange,
  getThisWeekRange,
  getTodayRange,
  resolveQuickRangePreset,
  validatePeriodRange,
} from "./dateRange";

describe("dateRange", () => {
  it("default range spans 12 calendar months", () => {
    const ref = new Date(2026, 6, 6);
    const range = getDefaultLast12MonthsRange(ref);
    expect(range.start_date).toBe("2025-08-01");
    expect(range.end_date).toBe("2026-07-06");
  });

  it("last 6 months range spans 6 calendar months", () => {
    const ref = new Date(2026, 6, 6);
    const range = getDefaultLast6MonthsRange(ref);
    expect(range.start_date).toBe("2026-02-01");
    expect(range.end_date).toBe("2026-07-06");
  });

  it("this month range starts on first day of current month", () => {
    const ref = new Date(2026, 6, 6);
    const range = getThisMonthRange(ref);
    expect(range.start_date).toBe("2026-07-01");
    expect(range.end_date).toBe("2026-07-06");
  });

  it("today range is a single day", () => {
    const ref = new Date(2026, 6, 6);
    expect(getTodayRange(ref)).toEqual({
      start_date: "2026-07-06",
      end_date: "2026-07-06",
    });
  });

  it("this week range starts on Monday", () => {
    // 2026-07-08 = quarta
    const ref = new Date(2026, 6, 8);
    const range = getThisWeekRange(ref);
    expect(range.start_date).toBe("2026-07-06");
    expect(range.end_date).toBe("2026-07-08");
  });

  it("last 30 days includes today", () => {
    const ref = new Date(2026, 6, 30);
    const range = getDefaultLast30DaysRange(ref);
    expect(range.start_date).toBe("2026-07-01");
    expect(range.end_date).toBe("2026-07-30");
  });

  it("resolveQuickRangePreset covers all presets", () => {
    const ref = new Date(2026, 6, 6);
    expect(resolveQuickRangePreset("today", ref)).toEqual(getTodayRange(ref));
    expect(resolveQuickRangePreset("thisWeek", ref)).toEqual(getThisWeekRange(ref));
    expect(resolveQuickRangePreset("thisMonth", ref)).toEqual(getThisMonthRange(ref));
    expect(resolveQuickRangePreset("30d", ref)).toEqual(getDefaultLast30DaysRange(ref));
    expect(resolveQuickRangePreset("6m", ref)).toEqual(getDefaultLast6MonthsRange(ref));
    expect(resolveQuickRangePreset("12m", ref)).toEqual(getDefaultLast12MonthsRange(ref));
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
