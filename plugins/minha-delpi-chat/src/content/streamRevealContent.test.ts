import { describe, expect, it } from "vitest";

import {
  streamRevealCharsPerFrame,
  streamRevealSegmentDelayMs,
  streamRevealSkeletonMinMs,
} from "./streamRevealContent";

describe("streamRevealContent", () => {
  it("expõe charsPerFrame e skeletonMinMs", () => {
    expect(streamRevealCharsPerFrame()).toBeGreaterThan(0);
    expect(streamRevealSkeletonMinMs()).toBeGreaterThan(0);
  });

  it("define delay por kind de segmento", () => {
    expect(streamRevealSegmentDelayMs("markdown")).toBe(0);
    expect(streamRevealSegmentDelayMs("table")).toBeGreaterThan(0);
    expect(streamRevealSegmentDelayMs("kpi")).toBeGreaterThan(0);
  });
});
