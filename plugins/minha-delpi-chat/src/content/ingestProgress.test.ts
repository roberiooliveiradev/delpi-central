import { describe, expect, it } from "vitest";

import {
  ingestProgressFractionLabel,
  ingestProgressPercentLabel,
  resolveIngestProgressPercent,
} from "./ingestProgress";

describe("ingestProgress", () => {
  it("resolve percent from done and total", () => {
    expect(resolveIngestProgressPercent({ done: 3, total: 10 })).toBe(30);
    expect(resolveIngestProgressPercent({ done: 1, total: 3 })).toBe(33);
  });

  it("prefers explicit percent when provided", () => {
    expect(resolveIngestProgressPercent({ percent: 42, done: 1, total: 10 })).toBe(42);
  });

  it("returns null when progress is indeterminate", () => {
    expect(resolveIngestProgressPercent({})).toBeNull();
    expect(resolveIngestProgressPercent({ total: 0, done: 0 })).toBeNull();
  });

  it("clamps percent to 0–100", () => {
    expect(resolveIngestProgressPercent({ percent: 150 })).toBe(100);
    expect(resolveIngestProgressPercent({ percent: -5 })).toBe(0);
  });

  it("formats labels from attachments bundle", () => {
    expect(ingestProgressPercentLabel(75)).toBe("75%");
    expect(ingestProgressFractionLabel(2, 5)).toBe("2/5");
  });
});
