import { describe, expect, it } from "vitest";
import { initialExpenseDate, localInputDate } from "./dates";

describe("initial expense date (ticket #1597)", () => {
  const day = new Date(2026, 10, 16, 23, 45, 0);

  it("prefills local calendar date when report has no dates", () => {
    expect(localInputDate(day)).toBe("2026-11-16");
    expect(initialExpenseDate(null, null, day)).toBe("2026-11-16");
  });

  it("respects existing report period instead of today", () => {
    expect(initialExpenseDate(null, "2026-11-12", day)).toBe("2026-11-12");
  });

  it("respects original saved expense date when editing", () => {
    expect(initialExpenseDate("2026-09-08", "2026-11-12", day)).toBe("2026-09-08");
  });
});
