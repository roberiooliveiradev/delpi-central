import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  detectPeriodPreset,
  resolvePeriodPreset,
  todayIsoInTimeZone,
} from "./periodPreset.ts";

describe("periodPreset", () => {
  const now = new Date("2026-08-13T18:00:00.000Z"); // afternoon SP
  const today = todayIsoInTimeZone(now);

  it("resolvePeriodPreset today is a single day", () => {
    const range = resolvePeriodPreset("today", now);
    assert.ok(range);
    assert.equal(range.dateStart, today);
    assert.equal(range.dateEnd, today);
    assert.equal(range.competence, "2026-08");
  });

  it("resolvePeriodPreset this_week starts on Monday", () => {
    // 2026-08-13 is Thursday in SP → Monday 2026-08-10
    const range = resolvePeriodPreset("this_week", now);
    assert.ok(range);
    assert.equal(range.dateStart, "2026-08-10");
    assert.equal(range.dateEnd, today);
  });

  it("resolvePeriodPreset this_month uses first day through today", () => {
    const range = resolvePeriodPreset("this_month", now);
    assert.ok(range);
    assert.equal(range.dateStart, "2026-08-01");
    assert.equal(range.dateEnd, today);
    assert.equal(range.competence, "2026-08");
  });

  it("resolvePeriodPreset last_month is full previous month", () => {
    const range = resolvePeriodPreset("last_month", now);
    assert.ok(range);
    assert.equal(range.dateStart, "2026-07-01");
    assert.equal(range.dateEnd, "2026-07-31");
    assert.equal(range.competence, "2026-07");
  });

  it("resolvePeriodPreset this_quarter starts at quarter begin", () => {
    const range = resolvePeriodPreset("this_quarter", now);
    assert.ok(range);
    assert.equal(range.dateStart, "2026-07-01");
    assert.equal(range.dateEnd, today);
  });

  it("resolvePeriodPreset this_year uses Jan 1 through today", () => {
    const range = resolvePeriodPreset("this_year", now);
    assert.ok(range);
    assert.equal(range.dateStart, "2026-01-01");
    assert.equal(range.dateEnd, today);
    assert.equal(range.competence, "");
  });

  it("resolvePeriodPreset last_12_months starts 11 months back", () => {
    const range = resolvePeriodPreset("last_12_months", now);
    assert.ok(range);
    assert.equal(range.dateStart, "2025-09-01");
    assert.equal(range.dateEnd, today);
  });

  it("resolvePeriodPreset custom returns null", () => {
    assert.equal(resolvePeriodPreset("custom"), null);
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
    ]) {
      const range = resolvePeriodPreset(id, now);
      assert.ok(range);
      assert.equal(detectPeriodPreset(range.dateStart, range.dateEnd, now), id);
    }
    assert.equal(detectPeriodPreset("2026-01-01", "2026-02-01", now), "custom");
  });
});
