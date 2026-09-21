import { describe, expect, it } from "vitest";

import {
  detectPeriodPreset,
  resolveEffectivePeriodPreset,
  resolvePeriodPreset,
  todayIsoInTimeZone,
} from "./periodPreset";

describe("periodPreset", () => {
  const now = new Date("2026-08-13T18:00:00.000Z"); // afternoon SP
  const today = todayIsoInTimeZone(now);

  it("resolvePeriodPreset today is a single day", () => {
    const range = resolvePeriodPreset("today", now);
    expect(range).toBeTruthy();
    expect(range?.dateStart).toBe(today);
    expect(range?.dateEnd).toBe(today);
    expect(range?.competence).toBe("2026-08");
  });

  it("resolvePeriodPreset this_week starts on Monday", () => {
    const range = resolvePeriodPreset("this_week", now);
    expect(range).toBeTruthy();
    expect(range?.dateStart).toBe("2026-08-10");
    expect(range?.dateEnd).toBe(today);
    expect(range?.competence).toBe("");
  });

  it("resolvePeriodPreset this_month uses first day through today", () => {
    const range = resolvePeriodPreset("this_month", now);
    expect(range).toBeTruthy();
    expect(range?.dateStart).toBe("2026-08-01");
    expect(range?.dateEnd).toBe(today);
    expect(range?.competence).toBe("2026-08");
  });

  it("resolvePeriodPreset last_month is full previous month", () => {
    const range = resolvePeriodPreset("last_month", now);
    expect(range).toBeTruthy();
    expect(range?.dateStart).toBe("2026-07-01");
    expect(range?.dateEnd).toBe("2026-07-31");
    expect(range?.competence).toBe("2026-07");
  });

  it("resolvePeriodPreset this_quarter is full civil quarter", () => {
    const range = resolvePeriodPreset("this_quarter", now);
    expect(range).toBeTruthy();
    expect(range?.dateStart).toBe("2026-07-01");
    expect(range?.dateEnd).toBe("2026-09-30");
    expect(range?.competence).toBe("");
  });

  it("resolvePeriodPreset this_quarter Q1 ends in March", () => {
    const feb = new Date("2026-02-10T18:00:00.000Z");
    const range = resolvePeriodPreset("this_quarter", feb);
    expect(range).toBeTruthy();
    expect(range?.dateStart).toBe("2026-01-01");
    expect(range?.dateEnd).toBe("2026-03-31");
  });

  it("resolvePeriodPreset this_year uses Jan 1 through today", () => {
    const range = resolvePeriodPreset("this_year", now);
    expect(range).toBeTruthy();
    expect(range?.dateStart).toBe("2026-01-01");
    expect(range?.dateEnd).toBe(today);
    expect(range?.competence).toBe("");
  });

  it("resolvePeriodPreset last_12_months starts 11 months back", () => {
    const range = resolvePeriodPreset("last_12_months", now);
    expect(range).toBeTruthy();
    expect(range?.dateStart).toBe("2025-09-01");
    expect(range?.dateEnd).toBe(today);
    expect(range?.competence).toBe("");
  });

  it("resolvePeriodPreset custom returns null", () => {
    expect(resolvePeriodPreset("custom")).toBeNull();
  });

  it("detectPeriodPreset recognizes resolved presets", () => {
    for (const id of [
      "today",
      "this_week",
      "this_month",
      "last_month",
      "this_quarter",
      "this_year",
      "last_12_months",
    ] as const) {
      const range = resolvePeriodPreset(id, now);
      expect(range).toBeTruthy();
      expect(detectPeriodPreset(range!.dateStart, range!.dateEnd, now)).toBe(id);
    }
    expect(detectPeriodPreset("2026-01-01", "2026-02-01", now)).toBe("custom");
  });

  it("resolveEffectivePeriodPreset keeps this_week on Monday when stored", () => {
    const monday = new Date("2026-08-17T18:00:00.000Z");
    const week = resolvePeriodPreset("this_week", monday);
    const day = resolvePeriodPreset("today", monday);
    expect(week).toBeTruthy();
    expect(day).toBeTruthy();
    expect(week?.dateStart).toBe(day?.dateStart);
    expect(week?.dateEnd).toBe(day?.dateEnd);
    expect(
      resolveEffectivePeriodPreset(week!.dateStart, week!.dateEnd, "this_week", monday),
    ).toBe("this_week");
    expect(
      resolveEffectivePeriodPreset(day!.dateStart, day!.dateEnd, "today", monday),
    ).toBe("today");
    expect(detectPeriodPreset(week!.dateStart, week!.dateEnd, monday)).toBe("today");
  });
});
