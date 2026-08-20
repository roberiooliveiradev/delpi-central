import { describe, expect, it } from "vitest";

import { formatIsoDate, formatIsoDayMonth } from "./formatIsoDate";

describe("formatIsoDate", () => {
  it("formats ISO dates without shifting the timezone", () => {
    expect(formatIsoDate("2026-08-20")).toBe("20/08/2026");
    expect(formatIsoDate("2026-01-01T00:00:00")).toBe("01/01/2026");
  });

  it("returns the empty marker for missing values", () => {
    expect(formatIsoDate(null)).toBe("—");
    expect(formatIsoDate("")).toBe("—");
    expect(formatIsoDate("20/08/2026")).toBe("—");
  });
});

describe("formatIsoDayMonth", () => {
  it("keeps only day and month", () => {
    expect(formatIsoDayMonth("2026-08-20")).toBe("20/08");
    expect(formatIsoDayMonth(undefined)).toBe("—");
  });
});
