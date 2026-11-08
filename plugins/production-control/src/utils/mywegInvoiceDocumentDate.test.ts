import { describe, expect, it } from "vitest";

import { previousCalendarDayIso } from "./mywegInvoiceDocumentDate";

describe("previousCalendarDayIso", () => {
  it("returns the previous calendar day as YYYY-MM-DD", () => {
    expect(previousCalendarDayIso(new Date(2026, 10, 8, 15, 30))).toBe("2026-11-07");
  });

  it("crosses month boundary", () => {
    expect(previousCalendarDayIso(new Date(2026, 10, 1, 9, 0))).toBe("2026-10-31");
  });

  it("crosses year boundary", () => {
    expect(previousCalendarDayIso(new Date(2026, 0, 1, 0, 0))).toBe("2025-12-31");
  });
});
