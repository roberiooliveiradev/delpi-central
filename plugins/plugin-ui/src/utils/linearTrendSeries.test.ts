import { describe, expect, it } from "vitest";

import {
  buildLinearTrendValues,
  resolveCalendarBucketFraction,
  withLinearTrendField,
} from "./linearTrendSeries";

describe("buildLinearTrendValues incomplete buckets", () => {
  it("excludes incomplete fraction from fit by default", () => {
    // Complete 0,10,20 then partial 100 at fraction 0.5 — exclude ⇒ line ~ 0,10,20,30
    const trend = buildLinearTrendValues([0, 10, 20, 100], {
      incompleteBucketMode: "exclude",
      bucketFractions: [1, 1, 1, 0.5],
    });
    expect(trend[0]).toBeCloseTo(0, 6);
    expect(trend[1]).toBeCloseTo(10, 6);
    expect(trend[2]).toBeCloseTo(20, 6);
    expect(trend[3]).toBeCloseTo(30, 6);
  });

  it("weightByFraction uses full-period equivalent in the fit", () => {
    // Partial 50 at 0.5 → treat as 100; with 0,50,100 → slope 50
    const trend = buildLinearTrendValues([0, 50, 50], {
      incompleteBucketMode: "weightByFraction",
      bucketFractions: [1, 1, 0.5],
    });
    expect(trend[0]).toBeCloseTo(0, 6);
    expect(trend[1]).toBeCloseTo(50, 6);
    expect(trend[2]).toBeCloseTo(100, 6);
  });
});

describe("resolveCalendarBucketFraction", () => {
  it("returns 1 for past buckets and partial for current", () => {
    const asOf = new Date("2026-09-15T12:00:00");
    expect(resolveCalendarBucketFraction("2026-08-01", "2026-08-31", asOf)).toBe(1);
    expect(resolveCalendarBucketFraction("2026-10-01", "2026-10-31", asOf)).toBe(0);
    const mid = resolveCalendarBucketFraction("2026-09-01", "2026-09-30", asOf);
    expect(mid).toBeGreaterThan(0.4);
    expect(mid).toBeLessThan(0.6);
  });
});

describe("buildLinearTrendValues", () => {
  it("é determinístico em série normal", () => {
    const values = [10, 20, 30, 40];
    const first = buildLinearTrendValues(values);
    const second = buildLinearTrendValues(values);
    expect(first).toEqual(second);
    expect(first[0]).toBeCloseTo(10, 6);
    expect(first[3]).toBeCloseTo(40, 6);
  });

  it("ignora null/undefined/NaN no ajuste", () => {
    const trend = buildLinearTrendValues([0, null, 20, Number.NaN, 40]);
    expect(trend[0]).toBeCloseTo(0, 5);
    expect(trend[2]).toBeCloseTo(20, 5);
    expect(trend[4]).toBeCloseTo(40, 5);
    expect(trend).toHaveLength(5);
  });

  it("retorna nulls com um único ponto válido ou nenhum", () => {
    expect(buildLinearTrendValues([10])).toEqual([null]);
    expect(buildLinearTrendValues([null, undefined])).toEqual([null, null]);
    expect(buildLinearTrendValues([])).toEqual([]);
  });

  it("aceita valores negativos", () => {
    const trend = buildLinearTrendValues([-10, 0, 10]);
    expect(trend[0]).toBeCloseTo(-10, 6);
    expect(trend[1]).toBeCloseTo(0, 6);
    expect(trend[2]).toBeCloseTo(10, 6);
  });

  it("trata zero real como ponto válido e não como null", () => {
    const zeros = buildLinearTrendValues([0, 0, 0]);
    expect(zeros[0]).toBeCloseTo(0, 6);
    expect(zeros[1]).toBeCloseTo(0, 6);
    const mixed = buildLinearTrendValues([null, 0, 10]);
    expect(mixed[1]).toBeCloseTo(0, 5);
    expect(mixed[2]).toBeCloseTo(10, 5);
    expect(buildLinearTrendValues([null, undefined, Number.NaN])).toEqual([
      null,
      null,
      null,
    ]);
  });
});

describe("withLinearTrendField", () => {
  it("reads fractionKey from rows", () => {
    const rows = [
      { v: 0, f: 1 },
      { v: 10, f: 1 },
      { v: 20, f: 1 },
      { v: 100, f: 0.5 },
    ];
    const out = withLinearTrendField(rows, "v", "_t", {
      incompleteBucketMode: "exclude",
      fractionKey: "f",
    });
    expect(out[3]._t).toBeCloseTo(30, 6);
  });

  it("calcula tendência independente por série", () => {
    const rows = [
      { atual: 10, anterior: 20 },
      { atual: 20, anterior: 18 },
      { atual: 30, anterior: 16 },
    ];
    const withAtual = withLinearTrendField(rows, "atual", "_trend_atual");
    const withBoth = withLinearTrendField(
      withAtual,
      "anterior",
      "_trend_anterior",
    );
    expect(withBoth[0]._trend_atual).toBeLessThan(withBoth[2]._trend_atual as number);
    expect(withBoth[0]._trend_anterior).toBeGreaterThan(
      withBoth[2]._trend_anterior as number,
    );
    expect(withBoth[0].atual).toBe(10);
    expect(withBoth[0].anterior).toBe(20);
  });

  it("não aplica _bucketFraction quando fractionKey é omitido", () => {
    const rows = [
      { v: 10, _bucketFraction: 1 },
      { v: 20, _bucketFraction: 1 },
      { v: 10, _bucketFraction: 0.5 },
    ];
    const weighted = withLinearTrendField(rows, "v", "_t", {
      incompleteBucketMode: "weightByFraction",
      fractionKey: "_bucketFraction",
    });
    const skipped = withLinearTrendField(rows, "v", "_t", {
      incompleteBucketMode: "weightByFraction",
    });
    expect(skipped[2]._t).not.toBeCloseTo(Number(weighted[2]._t));
  });

  it("preserva zero real e ignora null nas pontas e no meio", () => {
    const rows = [
      { v: null },
      { v: 0 },
      { v: null },
      { v: 10 },
      { v: undefined },
    ];
    const out = withLinearTrendField(rows, "v", "_t");
    expect(out[1].v).toBe(0);
    expect(out[1]._t).not.toBeNull();
    expect(out.every((row) => row.v !== 0 || row._t != null)).toBe(true);
  });
});
