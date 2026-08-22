import { describe, expect, it } from "vitest";

import {
  toDelinquencyExclusiveEnd,
  validateDelinquencyPeriodRange,
} from "./delinquencyPeriod";

describe("toDelinquencyExclusiveEnd", () => {
  it("adds one day for the api-delpi exclusive limit", () => {
    expect(toDelinquencyExclusiveEnd("2026-08-21")).toBe("2026-08-22");
  });
});

describe("validateDelinquencyPeriodRange", () => {
  it("accepts same-month inclusive ranges", () => {
    expect(validateDelinquencyPeriodRange("2026-08-01", "2026-08-21")).toBeNull();
  });

  it("rejects partial ranges", () => {
    expect(validateDelinquencyPeriodRange("2026-08-01", null)).toBeTruthy();
  });
});
