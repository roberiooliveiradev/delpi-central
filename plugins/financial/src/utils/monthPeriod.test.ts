import { describe, expect, it } from "vitest";

import {
  isYearMonth,
  monthPeriodRange,
  normalizeYearMonth,
  previousYearMonth,
} from "./monthPeriod";

describe("isYearMonth", () => {
  it("accepts only AAAA-MM with a real month", () => {
    expect(isYearMonth("2026-09")).toBe(true);
    expect(isYearMonth("2026-01")).toBe(true);
    expect(isYearMonth("2026-12")).toBe(true);
    expect(isYearMonth("2026-13")).toBe(false);
    expect(isYearMonth("2026-00")).toBe(false);
    expect(isYearMonth("2026-9")).toBe(false);
    expect(isYearMonth("2026-09-01")).toBe(false);
    expect(isYearMonth(null)).toBe(false);
  });
});

describe("normalizeYearMonth", () => {
  it("converts the TOTVS compact month to the URL form", () => {
    expect(normalizeYearMonth("202608")).toBe("2026-08");
    expect(normalizeYearMonth("202512")).toBe("2025-12");
  });

  it("keeps an already canonical month untouched", () => {
    expect(normalizeYearMonth("2026-08")).toBe("2026-08");
  });

  it("rejects anything that is not a month", () => {
    expect(normalizeYearMonth("202613")).toBeNull();
    expect(normalizeYearMonth("20260801")).toBeNull();
    expect(normalizeYearMonth("2026-8")).toBeNull();
    expect(normalizeYearMonth(null)).toBeNull();
  });
});

describe("monthPeriodRange", () => {
  it("accepts the compact month coming from the expense series", () => {
    expect(monthPeriodRange("202602")).toEqual({
      startDate: "2026-02-01",
      endDate: "2026-02-28",
    });
  });

  it("closes the month on its calendar last day", () => {
    expect(monthPeriodRange("2026-09")).toEqual({
      startDate: "2026-09-01",
      endDate: "2026-09-30",
    });
    expect(monthPeriodRange("2026-01")).toEqual({
      startDate: "2026-01-01",
      endDate: "2026-01-31",
    });
  });

  it("resolves February on leap and common years", () => {
    expect(monthPeriodRange("2028-02")?.endDate).toBe("2028-02-29");
    expect(monthPeriodRange("2026-02")?.endDate).toBe("2026-02-28");
  });

  it("returns null for an invalid month", () => {
    expect(monthPeriodRange("2026-13")).toBeNull();
    expect(monthPeriodRange("")).toBeNull();
  });
});

describe("previousYearMonth", () => {
  it("walks back across the year boundary", () => {
    expect(previousYearMonth("2026-01")).toBe("2025-12");
    expect(previousYearMonth("2026-09")).toBe("2026-08");
    expect(previousYearMonth("2026-11")).toBe("2026-10");
  });

  it("returns null for an invalid month", () => {
    expect(previousYearMonth("2026-9")).toBeNull();
  });
});
