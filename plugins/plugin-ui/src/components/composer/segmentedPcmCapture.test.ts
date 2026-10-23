import { describe, expect, it } from "vitest";
import { resolveSegmentMs } from "./segmentedPcmCapture";

describe("resolveSegmentMs", () => {
  it("defaults to a flat 4000ms when nothing is configured", () => {
    expect(resolveSegmentMs(0)).toBe(4000);
    expect(resolveSegmentMs(5)).toBe(4000);
  });

  it("honors explicit segmentMs for every slice", () => {
    expect(resolveSegmentMs(0, { segmentMs: 3000 })).toBe(3000);
    expect(resolveSegmentMs(2, { segmentMs: 3000 })).toBe(3000);
  });

  it("uses firstSegmentMs only for the first slice", () => {
    const opts = { segmentMs: 3000, firstSegmentMs: 2000 };
    expect(resolveSegmentMs(0, opts)).toBe(2000);
    expect(resolveSegmentMs(1, opts)).toBe(3000);
    expect(resolveSegmentMs(9, opts)).toBe(3000);
  });

  it("falls back to segmentMs when firstSegmentMs is absent", () => {
    expect(resolveSegmentMs(0, { segmentMs: 2500 })).toBe(2500);
  });
});
