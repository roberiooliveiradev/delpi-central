import { describe, expect, it } from "vitest";

import {
  buildMonthGrid,
  previousCalendarDayIso,
  shiftMonth,
} from "./mywegInvoiceDocumentDate";

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

describe("buildMonthGrid", () => {
  it("builds 42 cells starting on Monday for November 2026", () => {
    const grid = buildMonthGrid(2026, 11);
    expect(grid).toHaveLength(42);
    expect(grid[0].iso).toBe("2026-10-26");
    expect(grid.find((cell) => cell.iso === "2026-11-01")?.inMonth).toBe(true);
    expect(grid[0].inMonth).toBe(false);
  });
});

describe("shiftMonth", () => {
  it("moves across year", () => {
    expect(shiftMonth(2026, 1, -1)).toEqual({ year: 2025, month: 12 });
    expect(shiftMonth(2025, 12, 1)).toEqual({ year: 2026, month: 1 });
  });
});
