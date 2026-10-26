import { describe, expect, it } from "vitest";

import { formatNextRunLabel, isScheduleOverdue } from "./format";

describe("schedule overdue labels", () => {
  const now = new Date("2026-10-26T12:00:00-03:00");

  it("flags nextRunAt in the past", () => {
    expect(isScheduleOverdue("2026-10-23T11:00:00.000Z", { now })).toBe(true);
    expect(isScheduleOverdue("2026-10-27T11:00:00.000Z", { now })).toBe(false);
  });

  it("annotates overdue next-run labels", () => {
    const label = formatNextRunLabel("2026-10-23T11:00:00.000Z", { now });
    expect(label).toContain("(atrasado)");
  });
});
