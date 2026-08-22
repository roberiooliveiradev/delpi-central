import { describe, expect, it } from "vitest";

import { formatIsoDate, formatIssueDate, formatPeriodRange, formatYearMonth } from "./formatDates";

describe("formatDates", () => {
  it("formats ISO and already localized dates", () => {
    expect(formatIsoDate("2026-08-22")).toBe("22/08/2026");
    expect(formatIsoDate("20260806")).toBe("06/08/2026");
    expect(formatIsoDate("12/08/2026")).toBe("12/08/2026");
  });

  it("normalizes issue date labels that arrive in ISO", () => {
    expect(formatIssueDate("2026-08-06", "2026-08-06")).toBe("06/08/2026");
    expect(formatIssueDate("2026-08-06", "06/08/2026")).toBe("06/08/2026");
  });

  it("formats year-month for chart axes in pt-BR", () => {
    expect(formatYearMonth("2026-08")).toBe("Ago/2026");
    expect(formatYearMonth("202608")).toBe("Ago/2026");
    expect(formatYearMonth("202601")).toBe("Jan/2026");
  });

  it("joins a period range", () => {
    expect(formatPeriodRange("2026-08-01", "2026-08-22")).toBe("01/08/2026 a 22/08/2026");
    expect(formatPeriodRange(null, null)).toBeNull();
  });
});
