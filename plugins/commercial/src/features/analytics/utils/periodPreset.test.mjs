import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  detectPeriodPreset,
  resolvePeriodPreset,
  todayIsoInTimeZone,
} from "./periodPreset.ts";

describe("periodPreset", () => {
  it("resolvePeriodPreset mtd uses first day of month through today in SP", () => {
    // 2026-08-13 15:00 UTC ≈ afternoon in SP
    const now = new Date("2026-08-13T18:00:00.000Z");
    const range = resolvePeriodPreset("mtd", now);
    assert.ok(range);
    assert.equal(range.dateStart, "2026-08-01");
    assert.equal(range.dateEnd, todayIsoInTimeZone(now));
    assert.equal(range.competence, "2026-08");
  });

  it("resolvePeriodPreset ytd uses Jan 1 through today", () => {
    const now = new Date("2026-08-13T18:00:00.000Z");
    const range = resolvePeriodPreset("ytd", now);
    assert.ok(range);
    assert.equal(range.dateStart, "2026-01-01");
    assert.equal(range.dateEnd, todayIsoInTimeZone(now));
    assert.equal(range.competence, "");
  });

  it("resolvePeriodPreset custom returns null", () => {
    assert.equal(resolvePeriodPreset("custom"), null);
  });

  it("detectPeriodPreset recognizes mtd and ytd", () => {
    const now = new Date("2026-03-15T15:00:00.000Z");
    const mtd = resolvePeriodPreset("mtd", now);
    const ytd = resolvePeriodPreset("ytd", now);
    assert.ok(mtd && ytd);
    assert.equal(detectPeriodPreset(mtd.dateStart, mtd.dateEnd, now), "mtd");
    assert.equal(detectPeriodPreset(ytd.dateStart, ytd.dateEnd, now), "ytd");
    assert.equal(detectPeriodPreset("2026-01-01", "2026-02-01", now), "custom");
  });
});
