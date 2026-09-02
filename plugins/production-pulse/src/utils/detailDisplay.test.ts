import { describe, expect, it } from "vitest";

import { isHardwareCounterReset, formatIssuedByUser, readingsToChartPoints } from "./detailDisplay";
import type { DeviceReading } from "../types/detail";

describe("readingsToChartPoints", () => {
  it("maps chronological readings to chart points", () => {
    const readings: DeviceReading[] = [
      {
        id: 2,
        deviceId: "d1",
        metrics: { counter: 12 },
        deltaMetrics: { counter: 2 },
        meta: {},
        source: "poll",
        recordedAt: "2026-09-01T14:01:00.000Z",
      },
      {
        id: 1,
        deviceId: "d1",
        metrics: { counter: 10 },
        deltaMetrics: { counter: 1 },
        meta: {},
        source: "poll",
        recordedAt: "2026-09-01T14:00:00.000Z",
      },
    ];

    const points = readingsToChartPoints(readings, "counter", "value");
    expect(points).toHaveLength(2);
    expect(points[0]?.y).toBe(10);
    expect(points[1]?.y).toBe(12);
  });
});

describe("formatIssuedByUser", () => {
  it("shows name and email when resolved by directory lookup", () => {
    expect(
      formatIssuedByUser({
        issuedBy: "3bfdd634-a3a5-41af-b6b3-607025c2bdf5",
        issuedByName: "Roberto",
        issuedByEmail: "roberto@delpi.com",
      }),
    ).toBe("Roberto · roberto@delpi.com");
  });

  it("never shows raw uuid when profile is missing", () => {
    expect(
      formatIssuedByUser({
        issuedBy: "3bfdd634-a3a5-41af-b6b3-607025c2bdf5",
      }),
    ).toBe("—");
  });

  it("falls back to non-uuid issuedBy values", () => {
    expect(formatIssuedByUser({ issuedBy: "unknown" })).toBe("unknown");
  });
});

describe("isHardwareCounterReset", () => {
  it("detects counter_reset meta from API", () => {
    expect(isHardwareCounterReset({ meta: { counter_reset: true } })).toBe(true);
    expect(isHardwareCounterReset({ meta: { counterReset: true } })).toBe(true);
    expect(isHardwareCounterReset({ meta: {} })).toBe(false);
  });
});
